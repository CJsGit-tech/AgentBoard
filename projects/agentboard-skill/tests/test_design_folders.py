from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_project import validate_folder
META='> Owner: Product Designer | Version: 0.1.0 | Status: draft | Last Updated: 2026-11-18\n\n'

class DesignFolderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name);self.folder=self.project/'docs/designs';self.folder.mkdir(parents=True)
        self.topic='''**Purpose:** Define one readable design concern.

**Related stories:** Cross-cutting.

**Required context:** None for this independent rule.

## Rules

- Preserve focus and provide explicit labels.
'''
        names=['navigation-layout.md','visual-system.md','accessibility.md','interaction-states.md']
        (self.folder/'README.md').write_text('# Design index\n\n'+META+'Confirmed direction: clean and minimal.\n\n| Task | Read | Required companion |\n| --- | --- | --- |\n'+''.join(f'| Work on {n} | [{n}]({n}) | See topic context |\n' for n in names))
        for n in names:(self.folder/n).write_text('# Topic\n\n'+META+self.topic)
    def inspect(self):return validate_folder(self.project,self.folder,'design')
    def test_valid_task_oriented_design_folder(self):self.assertEqual(self.inspect(),[])
    def test_topic_requires_purpose_story_and_context(self):
        file=self.folder/'visual-system.md';file.write_text('# Topic\n\n'+META+'Unstructured prose.')
        errors=self.inspect()
        self.assertTrue(any('Purpose' in e for e in errors));self.assertTrue(any('Required context' in e for e in errors))
    def test_long_topic_needs_splitting(self):
        file=self.folder/'visual-system.md';file.write_text(file.read_text()+'\n'+('detail '*700))
        self.assertTrue(any('concise' in e.lower() for e in self.inspect()))
    def test_unknown_story_reference_and_missing_core(self):
        (self.folder/'navigation-layout.md').unlink()
        file=self.folder/'accessibility.md';file.write_text(file.read_text().replace('Cross-cutting.','US-999'))
        errors=self.inspect()
        self.assertTrue(any('navigation-layout' in e for e in errors));self.assertTrue(any('US-999' in e for e in errors))
    def test_monolith_is_not_an_active_design_topic(self):
        (self.folder/'design-profile.md').write_text('# Full document\n\n'+META+self.topic)
        self.assertTrue(any('monolith' in e.lower() for e in self.inspect()))
