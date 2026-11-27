"""Markdown whitespace is document data, not name normalization."""
import unittest
from pydantic import ValidationError
from app.models import Document
from tests import test_contracts as fixtures


class DocumentContentRules(unittest.TestCase):
    def test_preserves_indentation_and_final_newline(self):
        source = '    indented code\n\n- [x] task\n'
        document = Document(name='Document', project='P', content=source)
        self.assertEqual(document.content, source)

    def test_rejects_whitespace_only_documents(self):
        for source in ['', '   ', '\n\t\n']:
            with self.assertRaises(ValidationError):
                Document(name='Document', project='P', content=source)


class DocumentContentIntegration(unittest.TestCase):
    setUp = fixtures.WorkspaceIntegration.setUp
    create = fixtures.WorkspaceIntegration.create

    def test_ui_create_update_readback_history_and_stale_write_preserve_source(self):
        project = self.create('projects', name='Whitespace fixture')['id']
        original = '\n    first code block\n\n- [x] original\n'
        document = self.create('documents', name='Source', project=project, content=original)
        self.assertEqual(document['content'], original)
        changed = '    updated code\n\n```python\nprint(1)\n```\n'
        path = '/api/documents/' + document['id']
        result = self.http.patch(path, json={'revision': 1, 'changes': {'content': changed}})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['content'], changed)
        stale = self.http.patch(path, json={'revision': 1, 'changes': {'content': 'lost update'}})
        self.assertEqual(stale.status_code, 409)
        blank = self.http.patch(path, json={'revision': 2, 'changes': {'content': ' \n\t'}})
        self.assertEqual(blank.status_code, 422)
        workspace = self.http.get('/api/workspace?view=export').json()
        saved = next(row for row in workspace['documents'] if row['id'] == document['id'])
        self.assertEqual(saved['content'], changed)
        history = next(row for row in workspace['activity'] if row['record'] == document['id'] and row['action'] == 'Updated')
        self.assertIn(['content', original, changed], history['changes'])
