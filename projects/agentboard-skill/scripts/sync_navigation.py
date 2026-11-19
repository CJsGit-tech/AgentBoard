#!/usr/bin/env python3
"""Derive README navigation from canonical story files and contract inventory.

Default is read-only. --write replaces only marked navigation blocks, preserving surrounding human-authored explanations.
"""
import argparse,json,os,re,tempfile
from pathlib import Path
from urllib.parse import urlsplit,unquote


def safe(project,relative):
    root=Path(project).resolve();path=root/relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:raise ValueError('Unsafe navigation path')
    for parent in (path,*path.parents):
        if parent==root.parent:break
        if parent.is_symlink():raise ValueError('Symlink not allowed: '+relative)
    return path


def block(text,key,table,allow_create=False):
    start=f'<!-- agentbuild:{key}:start -->';end=f'<!-- agentbuild:{key}:end -->'
    replacement=start+'\n'+table.rstrip()+'\n'+end
    positions={start:[],end:[]};offset=0;fence=None
    for line in text.splitlines(keepends=True):
        stripped=line.strip();match=re.match(r'(`{3,}|~{3,})',stripped)
        if match:
            token=match.group(1)
            if fence is None:fence=token
            elif token[0]==fence[0] and len(token)>=len(fence):fence=None
        elif fence is None and stripped in positions:
            positions[stripped].append((offset,offset+len(line.rstrip('\r\n'))))
        offset+=len(line)
    begins=positions[start];ends=positions[end]
    if not begins and not ends and allow_create:
        return text.rstrip()+'\n\n'+replacement+'\n'
    if len(begins)!=1 or len(ends)!=1 or ends[0][0]<begins[0][0]:
        raise ValueError('Missing/ambiguous navigation markers outside code fences; explicitly mark the intended table first')
    return text[:begins[0][0]]+replacement+text[ends[0][1]:]


def render(project):
    project=Path(project).resolve();updates={}
    def escape(value):return str(value).replace('|','\\|').replace('\n',' ')
    folder=safe(project,'docs/user-stories')
    if folder.is_dir():
        rows=['| Story | Title | Associated Features |','| --- | --- | --- |'];ids=set()
        for file in sorted(folder.glob('*.md')):
            if file.name=='README.md':continue
            safe(project,str(file.relative_to(project)))
            text=file.read_text();found=re.findall(r'^### (US-\d{3,}) — (.+)$',text,re.M)
            if len(found)!=1:raise ValueError('One stable story ID/title required: '+file.name)
            id,title=found[0]
            if id in ids:raise ValueError('Duplicate story ID: '+id)
            ids.add(id)
            if not file.name.startswith(id+'-'):raise ValueError('Story filename/ID mismatch')
            parts=text.split('- **Associated Features:**\n')
            if len(parts)!=2:raise ValueError('Missing associated features: '+id)
            features=re.findall(r'^  - (.+)$',parts[1],re.M)
            if not features:raise ValueError('Empty associated features: '+id)
            rows.append(f'| [{id}]({file.name}) | {escape(title)} | {escape(", ".join(features))} |')
        if ids:
            file=safe(project,'docs/user-stories/README.md')
            before=file.read_text() if file.exists() else '# User Stories\n'
            updates[file]=(before,block(before,'stories','\n'.join(rows),allow_create=not file.exists()))
    manifest_file=safe(project,'docs/technical-architecture/contracts/manifest.json')
    if manifest_file.is_file():
        manifest=json.loads(manifest_file.read_text());base=manifest_file.parent.parent
        catalog_path=manifest.get('mcp_catalog')
        if catalog_path:
            catalog=safe(project,str((base/catalog_path).relative_to(project)))
            data=json.loads(catalog.read_text());rows=['| Tool | Permission | Input/output schema | Input example | Output examples |','| --- | --- | --- | --- | --- |']
            example_rows=manifest.get('examples',[])
            for tool in sorted(data.get('tools',[]),key=lambda t:t['name']):
                name=tool['name'];links={}
                for kind in ('mcp-input','mcp-output'):
                    found=[e for e in example_rows if e.get('kind')==kind and e.get('tool')==name]
                    if not found:raise ValueError(name+': missing example binding '+kind)
                    parts=[]
                    for e in sorted(found,key=lambda e:e['path']):
                        target=safe(project,str((base/e['path']).relative_to(project)))
                        if not target.is_file():raise ValueError('Missing bound example: '+e['path'])
                        relative=os.path.relpath(target,catalog.parent)
                        label=Path(e['path']).name.removeprefix(name.replace('_','-')+'.').removesuffix('.json')
                        parts.append(f'[{escape(label)}]({relative})')
                    links[kind]=' · '.join(parts)
                references=[]
                for field,label in [('inputSchema','Input'),('outputSchema','Output')]:
                    reference=tool[field].get('$ref')
                    if reference:
                        uri=urlsplit(reference)
                        if uri.scheme or uri.netloc:raise ValueError('Navigation uses local schema refs only')
                        raw=catalog.parent/unquote(uri.path) if uri.path else catalog
                        for ancestor in (raw,*raw.parents):
                            if ancestor==project.parent:break
                            if ancestor.is_symlink():raise ValueError('Schema navigation may not use symlinks')
                        target=raw.resolve()
                        if not target.is_relative_to(base.resolve()):raise ValueError('Schema navigation escapes architecture')
                        safe(project,str(target.relative_to(project)))
                        if not target.is_file():raise ValueError('Missing tool schema')
                        references.append(f'[{label}]({os.path.relpath(target,catalog.parent)}'+('#'+uri.fragment if uri.fragment else '')+')')
                if not references:references=['[Inline schemas]('+catalog.name+')']
                rows.append(f'| `{escape(name)}` | {escape(tool["x-agentbuild-permission"])} | {" · ".join(references)} | {links["mcp-input"]} | {links["mcp-output"]} |')
            file=safe(project,str((catalog.parent/'README.md').relative_to(project)))
            before=file.read_text() if file.exists() else '# MCP Tool Contracts\n'
            updates[file]=(before,block(before,'mcp-tools','\n'.join(rows),allow_create=not file.exists()))
    return updates


def sync(project,write=False):
    try:
        if write:
            manifest=json.loads(safe(project,'project-manifest.json').read_text())
            if manifest.get('project',{}).get('local_storage_confirmed') is not True:raise PermissionError('Local storage consent is required before index writes')
        updates=render(project)
    except (OSError,ValueError,KeyError,TypeError) as exc:return {'changed':[],'errors':[str(exc)]}
    changed=[str(file.relative_to(Path(project).resolve())) for file,(old,new) in updates.items() if old!=new]
    errors=[]
    if write:
        for file,(old,new) in updates.items():
            if old==new:continue
            if file.exists() and file.read_text()!=old:
                errors.append('Navigation changed during update; retry: '+str(file));continue
            file.parent.mkdir(parents=True,exist_ok=True)
            temp=None
            try:
                with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=file.parent,delete=False) as stream:
                    temp=Path(stream.name);stream.write(new)
                os.replace(temp,file)
            finally:
                if temp and temp.exists():temp.unlink()
    return {'changed':changed,'errors':errors}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True)
    mode=p.add_mutually_exclusive_group();mode.add_argument('--write',action='store_true');mode.add_argument('--check',action='store_true')
    a=p.parse_args();result=sync(a.project,a.write);print(json.dumps(result,indent=2))
    return bool(result['errors'] or (result['changed'] and not a.write))


if __name__=='__main__':raise SystemExit(main())
