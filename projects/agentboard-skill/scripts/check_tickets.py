#!/usr/bin/env python3
"""Read-only ticket structure checks; does not verify reports or runtime evidence."""
import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

FIELDS = {
    'Role': {'FE', 'BE'}, 'Type': {'BUG', 'BUILD'},
    'Status': {'Open', 'In progress', 'Blocked', 'Done', 'Cancelled'},
    'Assignment': {'Confirmed', 'Provisional'},
}
BUG_STATES = {'Reported', 'Investigating', 'Confirmed', 'Not reproduced', 'Fixed', 'Not a bug'}

def links(text):
    return re.findall(r'(?<!!)\[[^\]]*\]\(([^\s)]+)\)', text)

def section(text, name):
    match = re.search(r'^## '+re.escape(name)+r'\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1).strip() if match else ''

def strip_frontmatter(text):
    if not text.startswith('---\n'): return text
    end=text.find('\n---\n',4)
    return text[end+5:].lstrip('\n') if end>=0 else text

def validate(project):
    project = Path(project).resolve()
    folder = project/'docs/tickets'
    errors = []
    if folder.is_symlink() or (project/'docs').is_symlink() or not folder.is_dir():
        return ['tickets: missing/unsafe docs/tickets folder']
    readme = folder/'README.md'
    if not readme.is_file() or readme.is_symlink():
        return ['tickets: missing regular README.md']
    files = sorted(folder.glob('*.md'))
    records = {}; edges = {}; ids = set()
    for file in files:
        label = 'tickets: '+file.name
        if file.is_symlink():
            errors.append(label+': symlink not allowed'); continue
        text = file.read_text()
        for target in links(text):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path: continue
            linked = file.parent/unquote(parsed.path)
            if (not linked.resolve().is_relative_to(project) or
                    any(x.is_symlink() for x in (linked, *linked.parents) if x == project or project in x.parents) or
                    not linked.is_file()):
                errors.append(label+': broken/unsafe link '+target)
        if file == readme: continue
        body = strip_frontmatter(text)
        title = re.match(r'# (T-\d{3,}) — .+\n', body)
        if not title or not re.fullmatch(r'T-\d{3,}-[a-z0-9]+(?:-[a-z0-9]+)*\.md', file.name):
            errors.append(label+': invalid ticket title/filename'); continue
        ident = title.group(1)
        if not file.name.startswith(ident+'-'): errors.append(label+': ID differs from filename')
        if ident in ids: errors.append(label+': duplicate ID '+ident)
        ids.add(ident)
        values = {}
        for key in (*FIELDS, 'Verification', 'Depends on', 'Estimate (days)', 'Estimate scope', 'Estimate basis'):
            matches = re.findall(r'^'+re.escape(key)+r': ([^\n]+)$', body, re.M)
            if len(matches) != 1: errors.append(label+': needs one '+key)
            values[key] = matches[0].strip() if len(matches) == 1 else ''
        estimate = values['Estimate (days)']
        if not re.fullmatch(r'(?:0|[1-9]\d*)(?:\.\d+)?', estimate) or not any(c in '123456789' for c in estimate):
            errors.append(label+': Estimate (days) must be a positive decimal')
        scopes = {'Build'} if values['Type'] == 'BUILD' else {'Investigation', 'Repair'}
        if values['Estimate scope'] not in scopes:
            errors.append(label+': invalid Estimate scope for type')
        if values['Type'] == 'BUG' and values['Verification'] in {'Reported', 'Investigating', 'Not reproduced'} and values['Estimate scope'] != 'Investigation':
            errors.append(label+': unverified BUG must estimate Investigation, not unknown repair')
        for key, allowed in FIELDS.items():
            if values[key] not in allowed: errors.append(label+': invalid '+key)
        allowed = BUG_STATES if values['Type'] == 'BUG' else {'Not applicable'}
        if values['Verification'] not in allowed: errors.append(label+': invalid Verification for type')
        for name in ['Outcome', 'Acceptance Criteria', 'Context'] + (['User Report'] if values['Type'] == 'BUG' else []):
            if not section(body, name): errors.append(label+': missing/empty '+name)
        deps = values['Depends on']
        edges[ident] = [] if deps == 'None' else [x.strip() for x in deps.split(',')]
        if values['Status'] == 'Done':
            if not section(body, 'Completion Evidence'): errors.append(label+': Done requires Completion Evidence')
            if values['Type'] == 'BUG' and values['Verification'] not in {'Fixed', 'Not a bug'}:
                errors.append(label+': unresolved BUG cannot be Done')
        records[file.resolve()] = ident
    indexed = {(readme.parent/unquote(urlsplit(t).path)).resolve() for t in links(readme.read_text())
               if not urlsplit(t).scheme and not urlsplit(t).netloc}
    for file, ident in records.items():
        if file not in indexed: errors.append('tickets: unindexed '+ident)
    if not records: errors.append('tickets: no ticket files')
    for ident, deps in edges.items():
        for dep in deps:
            if dep not in ids: errors.append(f'tickets: {ident} unknown dependency {dep}')
    visited = set(); active = set()
    def visit(ident):
        if ident in active:
            errors.append('tickets: dependency cycle at '+ident); return
        if ident in visited: return
        active.add(ident)
        for dep in edges.get(ident, []):
            if dep in edges: visit(dep)
        active.remove(ident); visited.add(ident)
    for ident in edges: visit(ident)
    return errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    issues = validate(args.project)
    for issue in issues: print('ERROR: '+issue)
    print('Ticket structure: '+('FAIL' if issues else 'PASS (facts and runtime evidence require review)'))
    raise SystemExit(bool(issues))
