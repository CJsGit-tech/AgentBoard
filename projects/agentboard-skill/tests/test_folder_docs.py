import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_project import validate_folder

STORY='''### US-001 — Create project

- **Story:**
  - As a builder, I want a project to organize work.
- **Acceptance Criteria:**
  - Saving creates a project.
- **Associated Features:**
  - Projects
'''

class FolderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name);self.folder=self.project/'docs/user-stories';self.folder.mkdir(parents=True)
        (self.folder/'README.md').write_text('# Stories\n\n[US-001](US-001-create.md)\n')
        (self.folder/'US-001-create.md').write_text(STORY)

    def inspect(self):
        return validate_folder(self.project,self.folder,'stories',{'Projects'})

    def test_valid_plain_folder(self):self.assertEqual(self.inspect(),[])

    def test_duplicate_story_ids(self):
        (self.folder/'duplicate.md').write_text(STORY)
        self.assertTrue(any('duplicate' in e.lower() for e in self.inspect()))

    def test_broken_link_and_missing_index_entry(self):
        (self.folder/'README.md').write_text('[Missing](missing.md)')
        errors=self.inspect()
        self.assertTrue(any('broken' in e.lower() for e in errors))
        self.assertTrue(any('README' in e for e in errors))

    def test_unknown_feature_and_wrong_filename(self):
        file=self.folder/'US-001-create.md';file.write_text(STORY.replace('  - Projects','  - Unknown'))
        file.rename(self.folder/'US-002-wrong.md')
        errors=self.inspect()
        self.assertTrue(any('feature' in e for e in errors))
        self.assertTrue(any('filename' in e for e in errors))

    def test_nested_architecture_indexes_are_reachable(self):
        from validate_project import REQUIRED_HEADINGS
        folder=self.project/'docs/technical-architecture';(folder/'contracts').mkdir(parents=True)
        (folder/'README.md').write_text('[Contracts](contracts/README.md)\n'+'\n'.join('## '+h+'\n\nExplained.' for h in REQUIRED_HEADINGS['architecture']))
        (folder/'contracts/README.md').write_text('[Schema notes](notes.md)')
        (folder/'contracts/notes.md').write_text('Shared schema reading guidance.')
        self.assertEqual(validate_folder(self.project,folder,'architecture'),[])

    def test_escaping_link_and_symlink_rejected(self):
        (self.folder/'README.md').write_text('[Outside](../../../outside.md)\n[US-001](US-001-create.md)')
        (self.project/'outside.md').write_text('outside')
        self.assertTrue(self.inspect())
        (self.folder/'external.md').symlink_to(self.project/'outside.md')
        self.assertTrue(any('symlink' in e.lower() for e in self.inspect()))
