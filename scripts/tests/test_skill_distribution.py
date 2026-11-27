import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load('installer', 'install-skill.py')
checks = load('checks', 'check-skills.py')


class DistributionTests(unittest.TestCase):
    def test_cli_scope_resolution(self):
        for host, directory in [('codex', '.agents'), ('claude', '.claude')]:
            for scope in ('project', 'personal'):
                with self.subTest(host=host, scope=scope), tempfile.TemporaryDirectory() as scratch:
                    base = Path(scratch)
                    command = [sys.executable, str(SCRIPTS / 'install-skill.py'), 'install',
                               '--host', host, '--scope', scope, '--project', str(base / 'project')]
                    result = subprocess.run(command, env={**os.environ, 'HOME': str(base)}, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    parent = base / 'project' if scope == 'project' else base
                    self.assertTrue((parent / directory / 'skills/agentbuild/SKILL.md').is_file())

    def test_symlink_is_not_removed(self):
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / 'agentbuild'
            target.symlink_to(installer.SOURCE, target_is_directory=True)
            with self.assertRaises(ValueError):
                installer.install(target, 'codex', 'uninstall')
            self.assertTrue(target.is_symlink())

    def test_source_bundle(self):
        checks.validate()

    def test_install_update_backup_uninstall_each_host(self):
        for host in ('codex', 'claude'):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as scratch:
                target = Path(scratch) / 'host' / 'skills' / 'agentbuild'
                installer.install(target, host, 'install')
                entry = (target / 'SKILL.md').read_text()
                self.assertEqual('disable-model-invocation: true' in entry, host == 'claude')
                self.assertEqual((target / 'agents/openai.yaml').is_file(), host == 'codex')
                self.assertEqual((target / 'references/claude-code.md').is_file(), host == 'claude')
                self.assertTrue((target / 'references/commands.md').is_file())
                installer.install(target, host, 'update')
                self.assertEqual(len(list((target.parent.parent / 'agentbuild-backups').iterdir())), 1)
                installer.install(target, host, 'uninstall')
                self.assertFalse(target.exists())

    def test_modified_files_and_unmanaged_folder_preserved(self):
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / 'agentbuild'
            target.mkdir()
            (target / 'custom.txt').write_text('keep')
            with self.assertRaises(ValueError):
                installer.install(target, 'codex', 'install')
            self.assertEqual((target / 'custom.txt').read_text(), 'keep')
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / 'skills' / 'agentbuild'
            installer.install(target, 'codex', 'install')
            (target / 'SKILL.md').write_text('customized')
            for action in ('update', 'uninstall'):
                with self.assertRaises(ValueError):
                    installer.install(target, 'codex', action)
            self.assertEqual((target / 'SKILL.md').read_text(), 'customized')

    def test_missing_installation_is_not_created_by_update(self):
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / 'agentbuild'
            with self.assertRaises(ValueError):
                installer.install(target, 'codex', 'update')
            self.assertFalse(target.exists())

    def test_workflow_contract_scenarios(self):
        # Static contract checks, not live model behavioral evaluation.
        root = installer.SOURCE
        scenarios = json.loads((SCRIPTS / 'tests/workflow-scenarios.json').read_text())
        for scenario in scenarios:
            with self.subTest(command=scenario['command']):
                guide = (root / 'references/commands.md').read_text()
                self.assertIn('## ' + scenario['command'], guide)
                contract = (root / scenario['contract']).read_text()
                for term in scenario['required_terms']:
                    self.assertIn(term.casefold(), contract.casefold())


if __name__ == '__main__':
    unittest.main()
