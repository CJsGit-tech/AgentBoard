#!/usr/bin/env python3
"""Read-only Create-Screens evidence gate; not a substitute for independent execution."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

EXCLUDE={'node_modules','.git','dist','build','.next','coverage','__pycache__','.venv','evidence','captures'}

def safe_file(project,rel):
    if not isinstance(rel,str) or not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:
        raise ValueError('evidence paths must be project-relative')
    project=project.resolve()
    path=project/rel
    if any(p.is_symlink() for p in [path,*path.parents] if p==project or project in p.parents):
        raise ValueError('symlink evidence/source paths are not allowed')
    if not path.resolve().is_relative_to(project.resolve()): raise ValueError('escaping path')
    return path

def fingerprint(project,source_root):
    root=safe_file(project,source_root)
    if not root.is_dir() or root.resolve()==project.resolve(): raise ValueError('source_root must be a frontend subdirectory')
    digest=hashlib.sha256();count=0
    for path in sorted(root.rglob('*')):
        rel=path.relative_to(root)
        if any(part in EXCLUDE for part in rel.parts): continue
        if path.is_symlink(): raise ValueError('source tree contains symlink')
        if path.is_file():
            digest.update(str(rel).encode()+b'\0'+hashlib.sha256(path.read_bytes()).digest());count+=1
    if not count: raise ValueError('source tree is empty')
    return digest.hexdigest()

CONTEXT_FINGERPRINT_VERSION = 2


def context_fingerprint(project):
    """Conservative requirement hash; ignore declared bookkeeping, not new scope."""
    project = Path(project).resolve()
    digest = hashlib.sha256(b'agentbuild-context-v2\0')
    for folder in ('docs', 'agents'):
        root = project/folder
        if root.is_symlink(): raise ValueError('context tree contains symlink')
        for path in sorted(root.rglob('*')):
            rel = path.relative_to(project)
            if rel.parts[:3] in {('docs', 'designs', 'screens'), ('docs', 'designs', 'mockups')}: continue
            if rel == Path('docs/review-report.md') or rel.parts[:2] == ('docs', 'reviews'): continue
            if path.is_symlink(): raise ValueError('context tree contains symlink')
            if not path.is_file(): continue
            body = path.read_bytes()
            if path.suffix == '.md':
                text = body.decode('utf-8')
                # Search metadata is not product scope; remove it before the requirements hash.
                frontmatter = re.match(r'^---\r?\n.*?\r?\n---\r?\n(?:\r?\n)?', text, re.S)
                if frontmatter:
                    text = text[frontmatter.end():]
                # Normalize only the document header, never quoted requirement/report text.
                header_parts = re.split(r'(?m)(?=^#{2,6} )', text, maxsplit=1)
                header_parts[0] = re.sub(r'(?m)^> (Owner:[^\n]+)$', lambda m: '> '+' | '.join(
                    x.strip() for x in m[1].split('|')
                    if not x.strip().startswith(('Version:', 'Last Updated:', 'Status:'))), header_parts[0])
                if re.search(r'(?m)^Owner:', header_parts[0]):
                    header_parts[0] = re.sub(r'(?m)^(?:Version|Last Updated|Status):[^\n]*\n?', '', header_parts[0])
                text = ''.join(header_parts)
                if rel.parts[:2] == ('docs', 'tickets'):
                    if path.name == 'README.md':
                        # Skip only a recognized derived inventory table, not human scope/policy.
                        kept = []; inventory = False
                        for line in text.splitlines():
                            cells = {c.strip().lower() for c in line.strip('|').split('|')}
                            cells = { {'fe/be': 'role', 'bug/build': 'type'}.get(c, c) for c in cells }
                            if line.startswith('|') and {'role', 'type', 'status', 'verification'}.issubset(cells):
                                inventory = True; continue
                            if inventory and line.startswith('|'): continue
                            inventory = False; kept.append(line)
                        text = '\n'.join(kept)
                    if path.name != 'README.md':
                        # Outcome, criteria and context remain requirements; execution results do not.
                        text = re.sub(r'(?ms)^## (?:Investigation|Completion Evidence)\s*\n.*?(?=^## |\Z)', '', text)
                        parts = re.split(r'(?m)(?=^## )', text, maxsplit=1)
                        parts[0] = re.sub(r'(?m)^(?:Status|Verification|Assignment|Depends on|Estimate \(days\)|Estimate scope|Estimate basis):[^\n]*\n?', '', parts[0])
                        text = ''.join(parts)
                body = text.strip().encode('utf-8')
            digest.update(str(rel).encode()+b'\0'+hashlib.sha256(body).digest())
    manifest = safe_file(project, 'project-manifest.json')
    if manifest.is_file():
        data = json.loads(manifest.read_text())
        if not isinstance(data, dict): raise ValueError('manifest must be an object')
        # Preserve unknown/semantic configuration. Only explicitly incidental fields go.
        data.pop('change_impact', None)
        for key in ('updated_at',): data.pop(key, None)
        for key in ('updated_at', 'local_storage_confirmed_at', 'agentboard_project_id', 'sync_state'):
            data.get('project', {}).pop(key, None)
        artifacts = data.get('artifacts', {})
        for key in ('tickets', 'review'): artifacts.pop(key, None)
        for item in artifacts.values():
            if isinstance(item, dict):
                for key in ('updated_at', 'version', 'state', 'agentboard_document_id'): item.pop(key, None)
        for item in data.get('agents', {}).values():
            if isinstance(item, dict):
                for key in ('state', 'agentboard_agent_id'): item.pop(key, None)
        digest.update(json.dumps(data, sort_keys=True, separators=(',', ':')).encode())
    return digest.hexdigest()


def guidance_skill_path(project=None, explicit=None):
    """Find a matching installed entrypoint; an invalid override never falls back."""
    override = explicit or os.environ.get('AGENTBUILD_GUIDANCE_SKILL')
    candidates = []
    if override:
        path = Path(override).expanduser()
        candidates = [path/'SKILL.md' if path.is_dir() else path]
    else:
        base = Path(project or Path.cwd()).resolve()
        for parent in (base, *base.parents):
            for folder in ('.agents/skills', '.claude/skills'):
                candidates.append(parent/folder/'modern-web-guidance/SKILL.md')
        if os.environ.get('CODEX_HOME'):
            candidates.append(Path(os.environ['CODEX_HOME']).expanduser()/'skills/modern-web-guidance/SKILL.md')
        for folder in ('.agents/skills', '.claude/skills', '.codex/skills'):
            candidates.append(Path.home()/folder/'modern-web-guidance/SKILL.md')
    candidates = list(dict.fromkeys(candidates))
    for path in candidates:
        try:
            text = path.read_text()
            header = re.match(r'^---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
            if header and re.search(r'(?m)^name:\s*[\'\"]?modern-web-guidance[\'\"]?\s*$', header[1]): return path
        except (OSError, UnicodeError): pass
    reason = 'invalid Modern Web Guidance override' if override else 'Modern Web Guidance not found; searched'
    raise ValueError(reason+': '+', '.join(str(p) for p in candidates))

def validate(project, guidance_skill=None):
    errors=[]
    try:
        data=json.loads(safe_file(project,'docs/designs/screens/evidence/latest.json').read_text())
        def require(ok,message):
            if not ok: errors.append(message)
        def evidence_file(rel):
            f=safe_file(project,rel)
            require(f.is_file() and f.stat().st_size>0,f'missing/empty evidence: {rel}')
        dependency=guidance_skill_path(project, explicit=guidance_skill)
        require(dependency.is_file(),'required Modern Web Guidance skill is not installed/readable')
        guidance=data.get('guidance',{})
        nonweb=guidance.get('status')=='not_applicable' and bool(guidance.get('reason')) and data.get('target_platform') in ('ios','native')
        require(nonweb or (guidance.get('status')=='reviewed' and bool(guidance.get('guides')) and bool(guidance.get('cli_version')) and bool(guidance.get('skill_version'))),'Modern Web Guidance review evidence missing/incomplete')
        evidence_file(guidance.get('report'))
        require(data.get('schema_version')==1,'unsupported evidence schema')
        require(data.get('status')=='verified_pending_review','status must be verified_pending_review')
        expected=fingerprint(project,data.get('source_root'))
        require(data.get('source_fingerprint')==expected,'source changed or fingerprint is missing; rerun affected checks and review')
        legacy=data.get('legacy_scan',{})
        require(legacy.get('status')=='reviewed' and legacy.get('source_fingerprint')==expected,'legacy scan/review missing or stale')
        evidence_file(legacy.get('raw_output'))
        evidence_file(legacy.get('report'))
        require(data.get('context_fingerprint_version')==CONTEXT_FINGERPRINT_VERSION,'context fingerprint policy changed/missing; independent applicability review required before migrating evidence')
        context=context_fingerprint(project)
        require(data.get('context_fingerprint')==context,'project requirements/roles changed; refresh checks and independent review')
        builder=data.get('builder',{});reviewer=data.get('reviewer',{})
        require(bool(builder.get('agent_id')) and bool(reviewer.get('agent_id')) and builder.get('agent_id')!=reviewer.get('agent_id'),'builder and reviewer must have distinct real agent IDs')
        require(builder.get('role_file')=='agents/frontend-programmer.md','builder role must be project frontend-programmer')
        require(reviewer.get('role_file')=='agents/code-reviewer.md','reviewer role must be project code-reviewer')
        for role in (builder,reviewer): evidence_file(role.get('role_file'))
        require(reviewer.get('independent') is True,'independent reviewer required')
        require(reviewer.get('verdict')=='pass','reviewer verdict must pass')
        require(reviewer.get('source_fingerprint')==expected,'reviewer did not review current source')
        require(reviewer.get('context_fingerprint')==context,'reviewer did not review current project requirements')
        evidence_file(reviewer.get('report'))
        checks=data.get('checks',[])
        require(isinstance(checks,list) and bool(checks),'automated checks missing')
        check_ids=[c.get('id') for c in checks]
        require(all(check_ids) and len(check_ids)==len(set(check_ids)),'check IDs must be present and unique')
        for name in ('build','typecheck','ui','output-consistency','legacy-scan'):
            matches=[c for c in checks if c.get('kind')==name]
            require(bool(matches),f'missing check: {name}')
            for c in matches:
                na=name=='typecheck' and c.get('status')=='not_applicable' and bool(c.get('reason'))
                require(na or (c.get('status')=='pass' and c.get('exit_code')==0),f'failed/incomplete check: {name}')
                require(bool(c.get('command')) and bool(c.get('cwd')) and bool(c.get('finished_at')),f'missing command/working directory/time: {name}')
                evidence_file(c.get('log'))
        screens=data.get('screens',[])
        require(isinstance(screens,list) and bool(screens),'screen inventory empty')
        ids=[]
        for screen in screens:
            ids.append(screen.get('id'))
            require(bool(screen.get('id')) and bool(screen.get('requirements')),'screen needs identity and requirement references')
            require(screen.get('status')=='verified',f'unverified screen: {screen.get("id")}')
            evidence_file(screen.get('source'))
            require(safe_file(project,screen.get('source')).resolve().is_relative_to(safe_file(project,data['source_root']).resolve()),'screen source must be inside fingerprinted frontend root')
            require(bool(screen.get('captures')) and bool(screen.get('ui_checks')),'screen needs captures and UI check references')
            for capture in screen.get('captures',[]): evidence_file(capture)
            known={c.get('id') for c in checks if c.get('kind')=='ui' and c.get('status')=='pass'}
            require(all(x in known for x in screen.get('ui_checks',[])),'screen references missing/pending UI check')
        require(len(ids)==len(set(ids)),'duplicate screen IDs')
        require(not data.get('unresolved_required_items'),'required items remain unresolved')
    except (OSError,ValueError,TypeError,KeyError,AttributeError) as exc:
        errors.append(f'invalid/incomplete evidence: {exc}')
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',type=Path,required=True);parser.add_argument('--fingerprint',metavar='SOURCE_ROOT');parser.add_argument('--context-fingerprint',action='store_true');parser.add_argument('--guidance-skill',type=Path,help='installed guidance SKILL.md or folder; overrides discovery')
    args=parser.parse_args();project=args.project.resolve()
    if args.context_fingerprint:
        try: print(context_fingerprint(project));return 0
        except (OSError,ValueError,AttributeError,TypeError) as exc: print('ERROR:',exc);return 1
    if args.fingerprint:
        try: print(fingerprint(project,args.fingerprint));return 0
        except (OSError,ValueError) as exc: print(exc);return 1
    errors=validate(project, args.guidance_skill)
    for error in errors: print('ERROR:',error)
    print('Screen evidence gate: '+('FAIL' if errors else 'PASS (structure/freshness only; independent review remains required)'))
    return int(bool(errors))
if __name__=='__main__': raise SystemExit(main())
