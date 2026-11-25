"""Install/update/remove the canonical AgentBuild bundle for one local host."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time

SOURCE = Path(__file__).resolve().parents[1] / 'skills' / 'agentbuild'
MARKER = '.agentbuild-install.json'


def hashes(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file() and p.name != MARKER}


def install(target, host, action):
    if target.is_symlink():
        raise ValueError('Refusing to replace a symlink. Remove or relocate it yourself first.')
    if target.exists():
        marker = target / MARKER
        if not marker.is_file():
            raise ValueError('Existing folder is not managed by this installer; move it aside first.')
        state = json.loads(marker.read_text())
        if state.get('host') != host or state.get('files') != hashes(target):
            raise ValueError('Installed files changed or belong to another host; preserve them before continuing.')
        if action == 'install':
            raise ValueError('Already installed. Use update.')
    elif action != 'install':
        raise ValueError('No managed installation exists at this location.')
    if action == 'uninstall':
        shutil.rmtree(target)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as scratch:
        staged = Path(scratch) / 'agentbuild'
        shutil.copytree(SOURCE, staged, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        if host == 'claude':
            entry = staged / 'SKILL.md'
            entry.write_text(entry.read_text().replace('name: agentbuild\n', 'name: agentbuild\ndisable-model-invocation: true\n', 1))
        (staged / MARKER).write_text(json.dumps({'host': host, 'files': hashes(staged)}, indent=2))
        if target.exists():
            backup = target.parent.parent / 'agentbuild-backups' / str(time.time_ns())
            backup.parent.mkdir(parents=True, exist_ok=True)
            target.rename(backup)
            print('Previous version backed up:', backup)
        staged.rename(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'update', 'uninstall'])
    parser.add_argument('--host', choices=['codex', 'claude'], required=True)
    parser.add_argument('--scope', choices=['project', 'personal'], default='project')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    args = parser.parse_args()
    base = args.project.resolve() if args.scope == 'project' else Path.home()
    target = base / ('.agents' if args.host == 'codex' else '.claude') / 'skills' / 'agentbuild'
    try:
        install(target, args.host, args.action)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, str(error) + '\n')
    print(args.action, target)
    print('MCP registration is separate; see README.md. Start a fresh host session if needed.')


if __name__ == '__main__':
    main()
