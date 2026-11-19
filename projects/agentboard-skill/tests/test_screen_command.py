from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_skill
from validate_project import validate_folder

class ScreenCommandTests(unittest.TestCase):
    def test_command_is_required_and_complete(self):
        self.assertIn('create-screens',validate_skill.COMMANDS)
        self.assertEqual(validate_skill.validate(),[])
        original=Path.is_file
        with patch.object(Path,'is_file',lambda p: False if p.name=='create-screens.md' else original(p)):
            self.assertTrue(any('create-screens' in e for e in validate_skill.validate()))

    def test_pending_mockup_notes_are_not_design_topics(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp);folder=project/'docs/designs';folder.mkdir(parents=True)
            meta='> Owner: Designer | Version: 1 | Status: draft | Last Updated: 2026-11-18\n'
            names=['navigation-layout.md','visual-system.md','accessibility.md','interaction-states.md']
            (folder/'README.md').write_text(meta+'\n'.join(f'[{n}]({n})' for n in names))
            for name in names:
                (folder/name).write_text(meta+'\n**Purpose:** Rules\n**Related stories:** Cross-cutting\n**Required context:** None.\n')
            notes=folder/'mockups/round-001/README.md';notes.parent.mkdir(parents=True)
            notes.write_text('Pending selection. No canonical links yet.\n'+'sample '*500)
            self.assertEqual(validate_folder(project,folder,'design'),[])

    def test_screen_review_notes_are_not_design_topics(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp);folder=project/'docs/designs';folder.mkdir(parents=True)
            meta='> Owner: Designer | Version: 1 | Status: draft | Last Updated: 2026-11-18\n'
            names=['navigation-layout.md','visual-system.md','accessibility.md','interaction-states.md']
            (folder/'README.md').write_text(meta+'\n'.join(f'[{n}]({n})' for n in names))
            for name in names:
                (folder/name).write_text(meta+'\n**Purpose:** Rules\n**Related stories:** Cross-cutting\n**Required context:** None.\n')
            notes=folder/'screens/README.md';notes.parent.mkdir()
            notes.write_text('Pending review. Source paths and coverage are auxiliary.\n'+'sample '*500)
            self.assertEqual(validate_folder(project,folder,'design'),[])
