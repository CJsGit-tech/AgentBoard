#!/usr/bin/env python3
"""Create/reuse a real, self-contained local AgentBuild project.

No network access or AgentBoard connection is needed, but first-time local
setup requires explicit user consent. Customized files are never overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_ROOT / 'assets' / 'templates' / 'project-manifest.json'
ROLES_DIR = SKILL_ROOT / 'roles'
ROLE_NAMES = (
    'product-manager', 'product-designer', 'solution-architect',
    'backend-programmer', 'frontend-programmer', 'code-reviewer',
)


def slugify(name: str) -> str:
    normalized = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', normalized).strip('-')[:64].strip('-')
    return slug or 'project-' + hashlib.sha256(name.encode('utf-8')).hexdigest()[:12]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def write_manifest(path: Path, data: dict) -> None:
    """Persist manifest safely enough for an ordinary single-process skill flow."""
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def ensure_roles(project_dir: Path, manifest: dict) -> bool:
    """Populate missing role charters without replacing project-customized roles."""
    changed = False
    roles_dir = project_dir / 'agents'
    if roles_dir.is_symlink():
        raise ValueError(f'Local agents directory cannot be a symlink: {roles_dir}')
    roles_dir.mkdir(exist_ok=True)
    agents = manifest.setdefault('agents', {})
    for role in ROLE_NAMES:
        dest = roles_dir / f'{role}.md'
        src = ROLES_DIR / f'{role}.md'
        if not src.is_file():
            raise ValueError(f'Missing bundled role definition: {src}')
        if dest.is_symlink():
            raise ValueError(f'Local agent charter cannot be a symlink: {dest}')
        if not dest.exists():
            shutil.copyfile(src, dest)
            changed = True
        entry = agents.setdefault(role, {})
        if entry.get('local_role_path') != f'agents/{role}.md':
            entry['local_role_path'] = f'agents/{role}.md'
            changed = True
        if not entry.get('agentboard_agent_id') and entry.get('state') in (None, 'pending', 'missing'):
            entry['state'] = 'defined_locally'
            changed = True
    return changed


def scaffold(name: str, root: Path | None = None, *, user_approved_local: bool = False) -> tuple[Path, bool]:
    """Return (project_path, was_created). Refuses first-time local writes without consent."""
    if not name or not name.strip():
        raise ValueError('Project name must not be empty')
    name = name.strip()
    root = (root or (Path.cwd() / 'projects')).expanduser().resolve()
    slug = slugify(name)
    project_dir = root / slug
    manifest_path = project_dir / 'project-manifest.json'

    if project_dir.exists():
        if not project_dir.is_dir() or project_dir.is_symlink():
            raise ValueError(f'Unsafe existing project folder: {project_dir}')
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise ValueError(f'Existing directory is not an AgentBuild project: {project_dir}')
        try:
            existing = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (ValueError, OSError) as exc:
            raise ValueError(f'Cannot read existing project manifest: {exc}') from exc
        existing_name = existing.get('project', {}).get('name')
        if existing_name != name:
            raise ValueError(f'Slug collision: existing={existing_name!r}, requested={name!r}')
        info = existing['project']
        confirmed_before = info.get('local_storage_confirmed') is True
        if not (user_approved_local or confirmed_before):
            raise PermissionError('Local project storage has not been approved. Ask the user first, '
                                  'then rerun with --user-approved-local after Yes.')
        # Upgrade older local project non-destructively, only after approval.
        if (project_dir / 'docs').is_symlink():
            raise ValueError('Local docs/ directory cannot be a symlink')
        (project_dir / 'docs').mkdir(exist_ok=True)
        changed = ensure_roles(project_dir, existing)
        if not confirmed_before:
            info['local_storage_confirmed'] = True
            info['local_storage_confirmed_at'] = utc_now()
            changed = True
        if 'storage_mode' not in info:
            info['storage_mode'] = 'local' if info.get('agentboard_project_id') is None else 'hybrid'
            changed = True
        if info['storage_mode'] == 'local' and info.get('sync_state') == 'pending_sync':
            # Pending sync is meaningful only if user intends to sync; offline now works autonomously.
            info['sync_state'] = 'local_only'
            changed = True
        if str(existing.get('schema_version', '1.0')) != '2.0':
            existing['schema_version'] = '2.0'
            changed = True
        if changed:
            info['updated_at'] = utc_now()
            write_manifest(manifest_path, existing)
        return project_dir, False

    if not user_approved_local:
        raise PermissionError('Local fallback requires explicit user approval. Ask Yes/No first, '
                              'then rerun with --user-approved-local after Yes.')
    root.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=False, exist_ok=False)
    (project_dir / 'docs').mkdir()
    data = json.loads(TEMPLATE.read_text(encoding='utf-8'))
    data['project'].update(
        name=name, slug=slug, storage_mode='local', updated_at=utc_now(),
        agentboard_project_id=None, sync_state='local_only',
        local_storage_confirmed=True, local_storage_confirmed_at=utc_now(),
    )
    ensure_roles(project_dir, data)
    write_manifest(manifest_path, data)
    return project_dir, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True, help='Project display name')
    parser.add_argument('--root', type=Path, default=Path.cwd() / 'projects',
                        help='Projects root; default: ./projects in active workspace')
    parser.add_argument('--user-approved-local', action='store_true',
                        help='Assert explicit user approval for initial local storage. Only set after Yes.')
    args = parser.parse_args()
    try:
        project, created = scaffold(args.name, args.root,
                                    user_approved_local=args.user_approved_local)
    except (ValueError, OSError, PermissionError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'{"Created" if created else "Reused"} local project: {project}')
    print('Storage: local (no AgentBoard dependency)')
    print(f'Role charters: {project / "agents"} (6 locally defined, not spawned subagents)')
    print(f'Documents: {project / "docs"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
