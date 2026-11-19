import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import architecture_documents as a


def confirmed(profiles=('web',)):
    p=a.make_plan(list(profiles))
    p['status']='confirmed'
    p['context']={k:'Confirmed in discovery; local deployment and documented preferences.' for k in p['context']}
    for item in p['optional'].values():item.update(mode='not-applicable',reason='No corresponding requirement in this product.',requirements=[])
    return p


class ArchitectureDocumentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name)/'project';self.project.mkdir()
        (self.project/'project-manifest.json').write_text(json.dumps({'project':{'name':'Demo','local_storage_confirmed':True},'artifacts':{}}))

    def test_profiles_select_only_relevant_documents(self):
        web=a.selected(confirmed())
        ios=a.selected(confirmed(('ios',)))
        both=a.selected(confirmed(('web','ios')))
        self.assertIn('web/frontend.md',web);self.assertNotIn('ios/app-structure.md',web)
        self.assertIn('ios/release.md',ios);self.assertNotIn('web/backend.md',ios)
        self.assertEqual(set(both),set(web)|set(ios))

    def test_unconfirmed_or_incomplete_plan_never_creates_docs(self):
        for plan in (a.make_plan(['web']),dict(confirmed(),context={}),dict(confirmed(),profiles=['android'])):
            with self.assertRaises(ValueError):a.scaffold(self.project,plan)
            self.assertFalse((self.project/'docs').exists())

    def test_optional_files_and_inline_contracts(self):
        p=confirmed();p['optional']['mcp-tools'].update(mode='file',reason='Agents operate records.',requirements=['US-001'])
        p['optional']['authentication'].update(mode='section',reason='One local session.',requirements=['US-001'],covered_in={'path':'security-privacy.md','heading':'Local Session Authentication'})
        docs=a.selected(p)
        self.assertIn('mcp-tools.md',docs);self.assertNotIn('authentication.md',docs)
        self.assertIn('Local Session Authentication',docs['security-privacy.md']['headings'])
        p['optional']['authentication']['covered_in']['path']='../escape.md'
        with self.assertRaises(ValueError):a.selected(p)

    def test_scaffold_rerun_preserves_existing_content_and_reports_conflicts(self):
        p=confirmed();a.scaffold(self.project,p)
        file=self.project/'docs/technical-architecture/web/frontend.md';file.write_text('My authored content')
        result=a.scaffold(self.project,p)
        self.assertEqual(file.read_text(),'My authored content')
        self.assertEqual(result['created'],[])
        changed=copy.deepcopy(p);changed['profiles']=['web','ios']
        with self.assertRaises(ValueError):a.scaffold(self.project,changed)
        self.assertFalse((file.parent.parent/'ios').exists())

    def test_local_consent_and_symlinks(self):
        manifest=self.project/'project-manifest.json';m=json.loads(manifest.read_text());m['project']['local_storage_confirmed']=False;manifest.write_text(json.dumps(m))
        with self.assertRaises(PermissionError):a.scaffold(self.project,confirmed())
        self.assertFalse((self.project/'docs').exists())
        m['project']['local_storage_confirmed']=True;manifest.write_text(json.dumps(m))
        (self.project/'docs').symlink_to(Path(self.tmp.name))
        with self.assertRaises(ValueError):a.scaffold(self.project,confirmed())

    def test_skeleton_is_not_a_completed_document(self):
        a.scaffold(self.project,confirmed())
        errors=a.validate_documents(self.project/'docs/technical-architecture',self.project)
        self.assertTrue(any('skeleton' in e.lower() for e in errors))
        self.assertTrue(any('review' in e.lower() for e in errors))

    def test_project_folder_validator_rejects_skeleton_contracts(self):
        from validate_project import validate_folder
        a.scaffold(self.project,confirmed(('ios',)))
        errors=validate_folder(self.project,self.project/'docs/technical-architecture','architecture')
        self.assertTrue(any('skeleton' in e.lower() for e in errors))
        self.assertFalse(any('Frontend Folder Structure' in e for e in errors))

    def test_missing_rationale_and_directory_conflict_do_not_write(self):
        p=confirmed();p['optional']['realtime'].update(mode='file',reason='TODO: decide',requirements=['US-001'])
        with self.assertRaises(ValueError):a.scaffold(self.project,p)
        self.assertFalse((self.project/'docs').exists())
        directory=self.project/'docs/technical-architecture/system-architecture.svg';directory.mkdir(parents=True)
        with self.assertRaises(ValueError):a.scaffold(self.project,confirmed())
        self.assertFalse((directory.parent/'README.md').exists())

    def test_parent_file_conflict_is_detected_before_any_creation(self):
        folder=self.project/'docs/technical-architecture';folder.mkdir(parents=True)
        (folder/'web').write_text('Authored file')
        with self.assertRaises(ValueError):a.scaffold(self.project,confirmed())
        self.assertEqual(sorted(p.name for p in folder.iterdir()),['web'])

    def test_inline_topics_preserve_core_and_each_other(self):
        p=confirmed()
        p['optional']['authentication'].update(mode='section',reason='Local identity.',requirements=['US-001'],covered_in={'path':'security-privacy.md','heading':'Trust and Access'})
        p['optional']['approval-flow'].update(mode='section',reason='Human control.',requirements=['US-001'],covered_in={'path':'security-privacy.md','heading':'Trust and Access'})
        prompt=a.selected(p)['security-privacy.md']['prompts']['Trust and Access']
        self.assertIn('trust boundaries',prompt)
        self.assertIn('authentication',prompt)
        self.assertIn('approval-flow',prompt)

    def test_coverage_and_review_gate(self):
        p=confirmed();folder=self.project/'docs/technical-architecture';a.scaffold(self.project,p)
        for path,contract in a.selected(p).items():
            (folder/path).write_text('# '+contract['title']+'\n\n> Owner: Architect | Version: 0.1.0 | Status: draft | Last Updated: 2026-11-18\n\n'+'\n\n'.join('## '+h+'\n\nSpecific design and failure handling for this concern.' for h in contract['headings']))
        # README must link selected documents; diagram needs actual content.
        with (folder/'README.md').open('a') as f:
            f.write('\n'+''.join(f'[{path}]({path})\n' for path in a.selected(p) if path!='README.md')+'[Diagram](system-architecture.svg)\n[Contracts](contracts/README.md)\n[Examples](examples/README.md)\n')
        (folder/'system-architecture.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"><title>System</title><rect/><rect/><path/><text>Flow</text></svg>')
        stories=self.project/'docs/user-stories';stories.mkdir();(stories/'US-001-test.md').write_text('### US-001 — Test\n- **Acceptance Criteria:**\n  - Saving works.\n  - Failure is visible.\n- **Associated Features:**\n  - Projects\n')
        p['review']={k:'Compared actual requirements and documented evidence.' for k in ('story_coverage','consistency','diagram','evidence')};p['review'].update(status='reviewed',findings=[])
        (folder/'document-plan.json').write_text(json.dumps(p))
        self.assertTrue(any('US-001' in e for e in a.validate_documents(folder,self.project)))
        p['coverage']={'US-001':{'1':['data-model.md'],'2':['web/frontend.md']}}
        (folder/'contracts/manifest.json').write_text(json.dumps({'schema_version':1,'status':'draft','scope':{name:{'applicable':False,'reason':'This fixture has no external interfaces or persistent records.'} for name in ('rest','mcp','data')},'openapi':None,'mcp_catalog':None,'schemas':[],'examples':[]}))
        (folder/'contracts/README.md').write_text('No contracts applicable to this static fixture; see manifest.json.')
        (folder/'examples/README.md').write_text('No record or interface examples applicable to this fixture.')
        (folder/'document-plan.json').write_text(json.dumps(p))
        self.assertEqual(a.validate_documents(folder,self.project),[])
        p['review']['findings']=[{'severity':'critical','status':'open','description':'Approval bypass'}]
        (folder/'document-plan.json').write_text(json.dumps(p))
        self.assertTrue(any('critical' in e.lower() for e in a.validate_documents(folder,self.project)))
