"""Incremental review invalidation must agree with a fresh requirements snapshot."""
import unittest
from unittest.mock import patch

from app import reviews
from app.db import connect
from tests import test_contracts as fixtures


class ReviewInvalidation(unittest.TestCase):
    setUp = fixtures.WorkspaceIntegration.setUp
    create = fixtures.WorkspaceIntegration.create

    def setUpProject(self):
        self.project = self.create('projects', name='Incremental review')['id']
        self.milestone = self.create('milestones', name='Milestone', project=self.project)['id']

    def document(self, name, **data):
        return self.create('documents', project=self.project, name=name, content='Initial content.', **data)

    def ticket(self, name, **data):
        return self.create('tickets', project=self.project, milestone=self.milestone, name=name, **data)

    def update(self, kind, row, **changes):
        result = self.http.patch('/api/' + kind + '/' + row['id'], json={'revision':row['revision'], 'changes':changes})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def current(self, row):
        with connect() as conn:
            return reviews.current(conn, row['id'])

    def assert_matches_full_check(self):
        with connect() as conn:
            for subject in conn.execute("SELECT * FROM records WHERE project=%s AND NOT deleted AND kind IN ('tickets','documents')",
                                        (self.project,)).fetchall():
                row = reviews.current(conn, subject['id'])
                if subject['kind'] == 'documents' and not reviews.tracked(subject, ()):
                    continue
                self.assertEqual(row['signature'], reviews.snapshot(conn, subject)[1], subject['data']['name'])

    def test_status_and_outputs_skip_snapshot_but_requirement_changes_only_recheck_the_ticket(self):
        self.setUpProject()
        doc = self.document('Requirements')
        first = self.ticket('First', documents=[doc['id']])
        second = self.ticket('Second', documents=[doc['id']])
        second_review = self.current(second)
        with patch.object(reviews, 'snapshot', wraps=reviews.snapshot) as snapshot:
            first = self.update('tickets', first, output_documents=[doc['id']], status='Blocked')
            self.assertEqual(snapshot.call_count, 0)
            first = self.update('tickets', first, description='Different requirements')
            self.assertEqual([call.args[1]['id'] for call in snapshot.call_args_list], [first['id']])
        self.assertEqual(second_review['id'], self.current(second)['id'])
        denied = self.http.patch('/api/tickets/'+first['id'], json={'revision':first['revision'],'changes':{'status':'Done'}})
        self.assertEqual(denied.status_code, 409)
        self.assert_matches_full_check()

    def test_adding_and_removing_tag_source_and_fallback_dependencies(self):
        self.setUpProject()
        self.create('documents', project=self.project, name='Tag Catalog', content='## home\nState: Active')
        core = self.document('Core', document_type='product-vision')
        source = self.document('Source')
        linked = self.document('Linked')
        rooted = self.ticket('Explicit context', documents=[linked['id']])
        tagged = self.ticket('Tagged', tags=['home'])
        fallback = self.ticket('No context')
        keep = self.ticket('Independent', documents=[core['id']])
        keep_review = self.current(keep)['id']
        prior = self.current(tagged)
        self.assertTrue(prior['snapshot']['missing_context'])

        linked = self.update('documents', linked, tags=['home'], source_documents=[source['id']])
        self.assert_matches_full_check()
        current = self.current(tagged)
        self.assertFalse(current['snapshot']['missing_context'])
        self.assertEqual({d['id'] for d in current['snapshot']['documents']}, {source['id'], linked['id']})
        self.assertEqual({d['id'] for d in self.current(rooted)['snapshot']['documents']}, {source['id'], linked['id']})

        before = self.current(fallback)['id']
        core2 = self.document('New core', document_type='user-story')
        self.assertNotEqual(before, self.current(fallback)['id'])
        self.assertIn(core2['id'], [d['id'] for d in self.current(fallback)['snapshot']['documents']])
        linked = self.update('documents', linked, tags=[], source_documents=[])
        self.assertTrue(self.current(tagged)['snapshot']['missing_context'])
        self.assertEqual({d['id'] for d in self.current(rooted)['snapshot']['documents']}, {linked['id']})
        self.assertEqual(self.current(keep)['id'], keep_review)
        self.assert_matches_full_check()

    def test_ticket_review_holds_its_running_edit_and_deletion_preserves_its_links(self):
        self.setUpProject()
        doc = self.document('Requirements')
        ticket = self.ticket('First', documents=[doc['id']])
        for subject in (doc, ticket):
            review = self.current(subject)
            assessment = {'conclusion':'Within scope','rationale':'Fixture is covered.',
                          'findings':[{'document_id':d['id'],'outcome':'No update needed','reason':'Covered.'}
                                      for d in review['snapshot']['documents']]}
            self.assertEqual(self.http.post('/api/reviews/'+review['id']+'/assess', json={
                'revision':review['revision'], 'assessment':assessment}).status_code, 200)
        run = self.create('runs', name='Implement', agent='Codex', project=self.project, ticket=ticket['id'], status='Running')
        ticket = self.update('tickets', ticket, description='A new condition.')
        with connect() as conn:
            stored = conn.execute('SELECT data FROM records WHERE id=%s', (run['id'],)).fetchone()
        self.assertEqual(stored['data']['status'], 'Waiting for input')
        response = self.http.delete('/api/tickets/'+ticket['id'], params={'revision':ticket['revision']})
        self.assertEqual(response.status_code, 409)

    def test_establishing_a_baseline_on_an_excluded_document_refreshes_its_dependents(self):
        self.setUpProject()
        doc = self.document('Evidence', document_type='review-evidence')
        ticket = self.ticket('Ticket', documents=[doc['id']])
        self.assertTrue(self.current(ticket)['snapshot']['missing_context'])
        review = self.http.post('/api/reviews/start/documents/'+doc['id'], json={
            'revision':doc['revision'], 'request':'Review these sources.'}).json()
        response = self.http.post('/api/reviews/'+review['id']+'/assess', json={
            'revision':review['revision'], 'assessment':{'conclusion':'Within scope','rationale':'Source verified.',
                'findings':[{'document_id':d['id'],'outcome':'No update needed','reason':'Covered.'}
                            for d in review['snapshot']['documents']]}})
        self.assertEqual(response.status_code, 200, response.text)
        snapshot = self.current(ticket)['snapshot']
        self.assertFalse(snapshot['missing_context'])
        self.assertEqual([d['id'] for d in snapshot['documents']], [doc['id']])
        self.assert_matches_full_check()
