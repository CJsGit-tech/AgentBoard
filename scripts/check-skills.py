"""Validate the source skill bundle without touching host installs or board data."""
import ast
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT / 'skills' / 'agentbuild'):
    entry = (root / 'SKILL.md').read_text()
    assert entry.startswith('---\n'), 'Missing frontmatter'
    metadata = yaml.safe_load(entry.split('---', 2)[1])
    assert metadata['name'] == root.name
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', metadata['name'])
    assert 0 < len(metadata['description']) <= 1024
    assert metadata['license'] == 'MIT' and (root / 'LICENSE.txt').is_file()
    assert len(metadata['compatibility']) <= 500
    assert isinstance(metadata['metadata']['version'], str)
    policy = yaml.safe_load((root / 'agents' / 'openai.yaml').read_text())
    assert policy['policy']['allow_implicit_invocation'] is False
    assert '$agentbuild' in policy['interface']['default_prompt']
    for path in root.rglob('*.md'):
        content = path.read_text()
        assert '/Users/' not in content, f'Personal host path in {path}'
        for link in re.findall(r'\]\(([^)]+)\)', content):
            target = link.split('#', 1)[0]
            if target and '://' not in target and not target.startswith('mailto:'):
                assert (path.parent / target).is_file(), f'Broken file link: {path}: {link}'
    for path in root.rglob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    print('Skill metadata, invocation policy, file links and Python syntax passed.')


if __name__ == '__main__':
    validate()
