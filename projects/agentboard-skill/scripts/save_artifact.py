#!/usr/bin/env python3
"""Save one generated AgentBuild document in a local project and track its version.

The *agent* must author real content first. This utility only persists it safely.
Existing different content requires --revise and is archived before replacement.
No remote operations, approvals, or subagent spawning occur here.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from scaffold_project import utc_now, write_manifest


def _bump_version(previous: str | None) -> str:
    if not previous:
        return '0.1.0'
    m = re.fullmatch(r'(\d+)\.(\d+)\.(\d+)', previous)
    if not m:
        raise ValueError(f'Cannot increment version {previous!r}; use semantic version X.Y.Z')
    a, b, c = map(int, m.groups())
    return f'{a}.{b}.{c + 1}'


def _safe_doc_path(project: Path, relpath: str) -> Path:
    rel = PurePosixPath(relpath.replace('\\', '/'))
    if rel.is_absolute() or len(rel.parts) < 2 or rel.parts[0] != 'docs' or any(x in ('.', '..') for x in rel.parts):
        raise ValueError(f'Artifact path must be under docs/: {relpath!r}')
    target = project.joinpath(*rel.parts)
    for parent in (target, *target.parents):
        if parent == project.parent:
            break
        if parent.is_symlink():
            raise ValueError(f'Symlinks are not valid artifact paths: {parent}')
    return target


def persist(project: Path, artifact_key: str, source: Path, *, revise: bool = False) -> tuple[Path, str, bool]:
    project = project.expanduser().resolve()
    manifest_path = project / 'project-manifest.json'
    if not manifest_path.is_file():
        raise ValueError(f'Project manifest not found: {manifest_path}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('project', {}).get('local_storage_confirmed') is not True:
        raise PermissionError('Local writes are not authorized for this project. '
                              'Ask for explicit local-storage consent, then run scaffold_project.py '
                              'with --user-approved-local before saving documents.')
    artifacts = manifest.get('artifacts', {})
    if artifact_key not in artifacts:
        raise ValueError(f'Unknown artifact {artifact_key!r}; choose one of {", ".join(artifacts)}')
    item = artifacts[artifact_key]
    if item.get('layout') == 'folder':
        raise ValueError('Folder artifact: edit individual Markdown files and README, then validate_project.py; do not replace the index with a full document')
    target = _safe_doc_path(project, item['path'])
    data = source.expanduser().read_bytes()
    if not data or not data.strip():
        raise ValueError('Cannot save empty documents')
    try:
        content = data.decode('utf-8')
    except UnicodeError as exc:
        raise ValueError('Documents must be UTF-8') from exc
    if target.suffix == '.svg':
        root = ET.fromstring(content)
        if root.tag.rsplit('}', 1)[-1] != 'svg':
            raise ValueError('SVG output must have a <svg> root')
    if target.suffix == '.json':
        json.loads(content)
    if target.exists() and not target.is_file():
        raise ValueError(f'Artifact destination not a file: {target}')
    if target.is_file() and target.read_bytes() == data:
        return target, item.get('version') or 'unversioned', False
    if target.is_file() and not revise:
        raise ValueError(f'Artifact exists and differs: {target}. Use --revise to archive and replace it.')

    current_version = item.get('version')
    new_version = _bump_version(current_version)
    if target.is_file():
        history_dir = project / 'history' / artifact_key
        if history_dir.is_symlink():
            raise ValueError(f'Unsafe history directory: {history_dir}')
        history_dir.mkdir(parents=True, exist_ok=True)
        archive = history_dir / f'{current_version or "unversioned"}{target.suffix}'
        if archive.exists():
            raise ValueError(f'Archive already exists, refusing to overwrite: {archive}')
        shutil.copyfile(target, archive)

    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + '.tmp')
    temp.write_bytes(data)
    temp.replace(target)
    item['state'] = 'draft'
    item['version'] = new_version
    item['updated_at'] = utc_now()
    manifest['project']['updated_at'] = utc_now()
    affected = sorted(k for k, v in artifacts.items() if artifact_key in v.get('depends_on', []))
    if affected and current_version is not None:
        change = {'source': artifact_key, 'new_version': new_version, 'affected': affected, 'status': 'needs_review'}
        manifest.setdefault('change_impact', []).append(change)
    write_manifest(manifest_path, manifest)
    return target, new_version, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True, help='Project folder with manifest')
    parser.add_argument('--artifact', required=True, help='Manifest artifact key, e.g. vision, stories, design')
    parser.add_argument('--source', type=Path, required=True, help='Newly authored UTF-8 file')
    parser.add_argument('--revise', action='store_true', help='Archive existing content before replacing')
    args = parser.parse_args()
    try:
        target, version, changed = persist(args.project, args.artifact, args.source, revise=args.revise)
    except (ValueError, OSError, PermissionError, ET.ParseError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    print(f'{"Saved" if changed else "Unchanged"}: {target} (version {version})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
