import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

import yaml

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('claude_installer', SCRIPTS / 'install-skill.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def anchors(path):
    return {re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
            for title in re.findall(r'^#+ +(.+)$', path.read_text(), re.M)}


class ClaudeSkillTests(unittest.TestCase):
    def test_bundle_metadata_links_and_contents(self):
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / 'skills' / 'agentbuild'
            installer.install(target, 'claude', 'install')
            metadata = yaml.safe_load((target / 'SKILL.md').read_text().split('---', 2)[1])
            self.assertEqual(metadata['name'], 'agentbuild')
            self.assertIs(metadata['disable-model-invocation'], True)
            self.assertLessEqual(len(metadata['description']), 1024)
            self.assertFalse((target / 'agents').exists())
            for relative in ('LICENSE.txt', 'scripts/publish_canvas.py', 'scripts/attach_visual.py'):
                self.assertTrue((target / relative).is_file(), relative)
            for path in target.rglob('*.md'):
                content = path.read_text()
                self.assertNotIn('/Users/', content)
                for link in re.findall(r'\]\(([^)]+)\)', content):
                    if '://' in link:
                        continue
                    name, _, anchor = link.partition('#')
                    other = path.parent / name if name else path
                    self.assertTrue(other.is_file(), f'{path.name}: {link}')
                    if anchor:
                        self.assertIn(anchor, anchors(other), f'{path.name}: {link}')

    def test_every_shared_reference_is_reachable_from_entry(self):
        entry = (installer.CLAUDE_SOURCE / 'SKILL.md').read_text()
        for path in (installer.SOURCE / 'references').glob('*.md'):
            self.assertIn(f'references/{path.name}', entry)


if __name__ == '__main__':
    unittest.main()
