import json
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import sync_navigation as n

class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name);(self.project/'project-manifest.json').write_text(json.dumps({'project':{'name':'Demo','local_storage_confirmed':True},'artifacts':{}}));self.folder=self.project/'docs/user-stories';self.folder.mkdir(parents=True)
        (self.folder/'README.md').write_text('# Stories\n\nHuman introduction.\n\n<!-- agentbuild:stories:start -->\n| Story | Title | Associated Features |\n| --- | --- | --- |\n| old | stale | old |\n<!-- agentbuild:stories:end -->\n\nHuman closing notes.\n')
        (self.folder/'US-001-build.md').write_text('### US-001 — Build project\n\n- **Story:**\n  - As a builder, I want a project.\n- **Acceptance Criteria:**\n  - A project is saved.\n- **Associated Features:**\n  - Projects\n')
    def test_detects_drift_without_writing(self):
        before=(self.folder/'README.md').read_text()
        self.assertTrue(n.sync(self.project)['changed'])
        self.assertEqual((self.folder/'README.md').read_text(),before)
    def test_regenerates_only_navigation_and_is_idempotent(self):
        result=n.sync(self.project,write=True);self.assertTrue(result['changed'])
        text=(self.folder/'README.md').read_text()
        self.assertIn('Human introduction.',text);self.assertIn('Human closing notes.',text)
        self.assertIn('US-001-build.md',text);self.assertNotIn('| old |',text)
        self.assertEqual(n.sync(self.project)['changed'],[])
    def test_new_story_updates_navigation(self):
        n.sync(self.project,write=True)
        new=(self.folder/'US-001-build.md').read_text().replace('US-001','US-002')
        (self.folder/'US-002-next.md').write_text(new)
        self.assertTrue(n.sync(self.project)['changed'])
        n.sync(self.project,write=True)
        self.assertIn('US-002-next.md',(self.folder/'README.md').read_text())
    def test_ambiguous_markers_and_symlinks_refuse_writes(self):
        file=self.folder/'README.md';file.write_text('<!-- agentbuild:stories:start -->\nBroken')
        result=n.sync(self.project,write=True);self.assertTrue(result['errors'])
        self.assertEqual(file.read_text(),'<!-- agentbuild:stories:start -->\nBroken')
        file.unlink();file.symlink_to(self.folder/'US-001-build.md')
        self.assertTrue(n.sync(self.project,write=True)['errors'])

    def test_unmarked_explanations_and_fenced_tables_are_never_replaced(self):
        base=self.project/'docs/technical-architecture';folder=base/'contracts/mcp';folder.mkdir(parents=True)
        catalog={'tools':[{'name':'read_record','inputSchema':{'$ref':'record.schema.json'},'outputSchema':{'$ref':'record.schema.json'},'x-agentbuild-permission':'read'}]}
        (folder/'tools.json').write_text(json.dumps(catalog));(folder/'record.schema.json').write_text('{"type":"object"}')
        examples=[]
        for kind in ('mcp-input','mcp-output'):
            relative='examples/'+kind+'.json';file=base/relative;file.parent.mkdir(exist_ok=True);file.write_text('{}')
            examples.append({'kind':kind,'tool':'read_record','path':relative})
        (base/'contracts/manifest.json').write_text(json.dumps({'mcp_catalog':'contracts/mcp/tools.json','examples':examples}))
        for text in ('# Human notes\n\n| Tool | Why approval is required |\n| --- | --- |\n| delete_project | Preserve this policy explanation |\n',
                     '# Example\n\n```markdown\n| Tool | Permission | Input/output schema | Input example | Output example |\n| --- | --- | --- | --- | --- |\n| example | read | sample | sample | sample |\n```\n'):
            (folder/'README.md').write_text(text)
            result=n.sync(self.project,write=True)
            self.assertTrue(result['errors'])
            self.assertEqual((folder/'README.md').read_text(),text)

    def test_unapproved_local_project_cannot_write_indexes(self):
        path=self.project/'project-manifest.json';data=json.loads(path.read_text());data['project']['local_storage_confirmed']=False;path.write_text(json.dumps(data))
        before=(self.folder/'README.md').read_text()
        self.assertTrue(n.sync(self.project,write=True)['errors'])
        self.assertEqual((self.folder/'README.md').read_text(),before)
