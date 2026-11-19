#!/usr/bin/env python3
"""Select and scaffold plain architecture documents; validate structural readiness.

No architecture is inferred or approved by this script. Plans come from confirmed
discovery. Skeletons are incomplete until authored and independently reviewed.
"""
from __future__ import annotations
import argparse
import copy
from datetime import date
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/'assets/architecture-documents.json'
MARKER='<!-- AGENTBUILD:SKELETON -->'


def catalog():return json.loads(CATALOG.read_text(encoding='utf-8'))


def make_plan(profiles):
    c=catalog()
    if not profiles or len(set(profiles))!=len(profiles) or any(p not in c['profiles'] for p in profiles):
        raise ValueError('Choose web, ios, or both once each')
    return {'schema_version':1,'status':'proposed','profiles':profiles,
        'context':dict.fromkeys(['deployment','stack','providers','integrations','data','security','operations'],''),
        'optional':{k:{'mode':'undecided','reason':'','requirements':[]} for k in c['optional']},
        'coverage':{},'review':{'status':'pending','story_coverage':'','consistency':'','diagram':'','evidence':'','findings':[]}}


def meaningful(value):
    return isinstance(value,str) and bool(value.strip()) and value.strip().lower() not in ('n/a','none','not applicable','tbd') and not re.search(r'AGENTBUILD:SKELETON|\[WRITE:|\bTODO:|\bTBD\b|<ProjectName>|<YYYY-MM-DD>',value,re.I)


def selected(plan):
    c=catalog()
    if plan.get('schema_version')!=1:raise ValueError('Unknown document plan schema')
    profiles=plan.get('profiles')
    if not isinstance(profiles,list) or not profiles or len(set(profiles))!=len(profiles) or any(p not in c['profiles'] for p in profiles):raise ValueError('Invalid platform profiles')
    docs=copy.deepcopy(c['core'])
    for p in profiles:docs.update(copy.deepcopy(c['profiles'][p]))
    decisions=plan.get('optional',{})
    if set(decisions)!=set(c['optional']):raise ValueError('Decide every optional topic, including explicit not-applicable reasons')
    inline=[]
    for id,item in decisions.items():
        if not isinstance(item,dict) or item.get('mode') not in ('file','section','not-applicable') or not meaningful(item.get('reason')):
            raise ValueError(f'{id}: choose file, section, or not-applicable and explain why')
        refs=item.get('requirements')
        if not isinstance(refs,list) or any(not meaningful(x) for x in refs):raise ValueError(f'{id}: invalid requirement references')
        if item['mode']!='not-applicable' and not refs:raise ValueError(f'{id}: provide triggering story/requirement references')
        if item['mode']=='file':
            document=copy.deepcopy(c['optional'][id]['document']);path=document.pop('path');docs[path]=document
        elif item['mode']=='section':inline.append((id,item))
    for id,item in inline:
        target=item.get('covered_in',{})
        if not isinstance(target,dict) or target.get('path') not in docs or not meaningful(target.get('heading')) or '\n' in target['heading']:
            raise ValueError(f'{id}: inline topic must identify a selected document and heading')
        contract=docs[target['path']];heading=target['heading']
        if heading not in contract['headings']:contract['headings'].append(heading)
        optional=c['optional'][id]['document']
        detail=' '.join(h+': '+optional['prompts'][h] for h in optional['headings'])
        addition='Optional concern '+id+': '+item['reason']+' '+detail
        contract['prompts'][heading]=(contract['prompts'].get(heading,'')+'\n\n'+addition).strip()
    return docs


def confirmed_plan(plan):
    docs=selected(plan)
    if plan.get('status')!='confirmed':raise ValueError('Document plan must be confirmed after discovery')
    context=plan.get('context',{})
    keys=make_plan(plan['profiles'])['context']
    if not isinstance(context,dict) or any(not meaningful(context.get(key)) for key in keys):raise ValueError('Complete the discovery context before confirming the plan')
    return docs


def safe(folder,relative):
    rel=PurePosixPath(relative)
    if rel.is_absolute() or any(x in ('.','..','') for x in relative.split('/')) or '\\' in relative:raise ValueError('Unsafe document path')
    path=folder.joinpath(*rel.parts)
    for parent in (path,*path.parents):
        if parent == folder.parent.parent: break
        if parent.is_symlink():raise ValueError('Symlink not allowed: '+str(parent))
        if parent != path and parent.exists() and not parent.is_dir():raise ValueError('Parent path conflicts with a file: '+str(parent))
    return path


def skeleton(path,contract,docs,project_name):
    title=contract['title']+' — '+project_name
    kind='architecture-index' if path=='README.md' else 'architecture-topic'
    metadata=['---','name: '+json.dumps(title,ensure_ascii=False),
        'description: '+json.dumps('Outlines architecture decisions and implementation guidance for this topic.' if path!='README.md' else 'Routes readers to the selected architecture topics and system diagram.',ensure_ascii=False),
        'kind: '+json.dumps(kind),'tags: []','---','']
    lines=metadata+['# '+title,'',
        '> Owner: Solution Architect | Version: 0.1.0 | Status: draft | Last Updated: '+date.today().isoformat(),'',MARKER,'']
    for heading in contract['headings']:
        lines+=['## '+heading,'','[WRITE: '+contract['prompts'][heading]+']','']
        if path=='README.md' and heading=='Document Navigation':
            lines += [f'- [{item["title"]}]({relative})' for relative,item in docs.items() if relative!='README.md']
            lines += ['- [Contracts](contracts/README.md)', '- [JSON examples](examples/README.md)', '- [System diagram](system-architecture.svg)','- [Confirmed document plan](document-plan.json)','']
    return '\n'.join(lines)+'\n'


def scaffold(project,plan):
    docs=confirmed_plan(plan)
    project=Path(project).expanduser().resolve()
    manifest=json.loads((project/'project-manifest.json').read_text())
    if manifest.get('project',{}).get('local_storage_confirmed') is not True:raise PermissionError('Local storage approval is required')
    folder=project/'docs/technical-architecture'
    # Preflight before creating any directory or file.
    for path in [*docs,'system-architecture.svg','document-plan.json','contracts/README.md','contracts/manifest.json','examples/README.md']:safe(folder,path)
    plan_file=folder/'document-plan.json'
    if plan_file.exists() and json.loads(plan_file.read_text())!=plan:raise ValueError('Existing document plan differs; review and explicitly revise it before scaffolding')
    for path in [*docs,'system-architecture.svg','document-plan.json','contracts/README.md','contracts/manifest.json','examples/README.md']:
        target=folder/path
        if target.exists() and not target.is_file():raise ValueError('Document path conflicts with a directory: '+path)
    payloads={path:skeleton(path,contract,docs,manifest['project']['name']) for path,contract in docs.items()}
    payloads['document-plan.json']=json.dumps(plan,ensure_ascii=False,indent=2)+'\n'
    payloads['system-architecture.svg']='<svg xmlns="http://www.w3.org/2000/svg" width="800" height="240"><title>Architecture skeleton</title><!-- AGENTBUILD:SKELETON --><text x="30" y="70">SKELETON: replace with the actual module architecture.</text></svg>\n'
    payloads['contracts/README.md']='---\nname: "Architecture Contracts"\ndescription: "Indexes the authoritative interface and data contracts."\nkind: "contract-index"\ntags: []\n---\n\n# Contracts\n\n'+MARKER+'\n\n[WRITE: Link the authoritative OpenAPI/JSON schemas, or explain why no interfaces/records apply. Register examples in manifest.json.]\n'
    payloads['examples/README.md']='---\nname: "Architecture JSON Examples"\ndescription: "Indexes schema-bound examples for records and interfaces."\nkind: "example-index"\ntags: []\n---\n\n# JSON Examples\n\n'+MARKER+'\n\n[WRITE: Link representative schema-bound examples and label records, HTTP bodies and MCP payloads distinctly.]\n'
    payloads['contracts/manifest.json']=json.dumps({'schema_version':1,'status':'skeleton','scope':{name:{'applicable':None,'reason':'[WRITE: Determine applicability from actual requirements.]'} for name in ('rest','mcp','data')},'openapi':None,'mcp_catalog':None,'schemas':[],'examples':[]},indent=2)+'\n'
    created=[];preserved=[];conflicts=[]
    for path,body in payloads.items():
        target=folder/path
        if target.exists():preserved.append(path);continue
        target.parent.mkdir(parents=True,exist_ok=True)
        try:
            with target.open('x',encoding='utf-8') as stream:stream.write(body)
            created.append(path)
        except FileExistsError:preserved.append(path)
    nav=(folder/'README.md').read_text()
    for path in docs:
        if path!='README.md' and f']({path})' not in nav:conflicts.append('Existing README needs link: '+path)
    return {'created':created,'preserved':preserved,'conflicts':conflicts,'status':'skeletons only; author and validate before reporting completed drafts'}


def story_criteria(project):
    project=Path(project)
    folder=project/'docs/user-stories'
    paths=sorted(folder.glob('*.md')) if folder.is_dir() else [project/'docs/user-stories.md']
    criteria={}
    for path in paths:
        if not path.is_file() or path.name=='README.md':continue
        if path.is_symlink():raise ValueError('Story source may not be a symlink')
        text=path.read_text()
        parts=re.split(r'^### +(US-\d{3,})[^\n]*\n',text,flags=re.M)
        for id,body in zip(parts[1::2],parts[2::2]):
            if id in criteria:raise ValueError('Duplicate story ID: '+id)
            match=re.search(r'^- \*\*Acceptance Criteria:\*\*\s*\n(.*?)(?=^- \*\*|\Z)',body,re.M|re.S)
            count=len(re.findall(r'^  - \S',match.group(1),re.M)) if match else 0
            criteria[id]=count
    return criteria


def validate_documents(folder,project):
    folder=Path(folder);project=Path(project);errors=[]
    try:
        plan_file=safe(folder,'document-plan.json')
        plan=json.loads(plan_file.read_text());docs=confirmed_plan(plan)
        stories=story_criteria(project)
        if not stories: errors.append('Missing usable User Stories for acceptance-criterion coverage')
        for path,contract in docs.items():
            target=safe(folder,path)
            if not target.is_file():errors.append('Missing selected document: '+path);continue
            text=target.read_text()
            if not meaningful(text):errors.append('Incomplete skeleton/placeholder: '+path)
            for key in ('Owner:','Version:','Status:','Last Updated:'):
                if key not in text[:1000]:errors.append(f'{path}: missing metadata {key}')
            sections=re.split(r'^## +(.+?)\s*$',text,flags=re.M)
            bodies=dict(zip(sections[1::2],sections[2::2]))
            for heading in contract['headings']:
                if heading not in bodies:errors.append(f'{path}: missing contracted section {heading}')
                elif not meaningful(bodies[heading]):errors.append(f'{path}: incomplete contracted section {heading}')
        nav=(folder/'README.md').read_text() if (folder/'README.md').is_file() else ''
        for path in [p for p in docs if p!='README.md']+['system-architecture.svg','contracts/README.md','examples/README.md']:
            if f']({path})' not in nav:errors.append('README missing selected document link: '+path)
        diagram=safe(folder,'system-architecture.svg')
        if not diagram.is_file():errors.append('Missing system diagram')
        else:
            data=diagram.read_text()
            try:
                root=ET.fromstring(data)
                if root.tag.rsplit('}',1)[-1]!='svg' or len(list(root.iter()))<5:errors.append('Diagram is not a meaningful SVG')
            except ET.ParseError:errors.append('Malformed system diagram SVG')
            if re.search('SKELETON|TEMPLATE',data,re.I):errors.append('Diagram is an incomplete skeleton')
        coverage=plan.get('coverage',{})
        if not isinstance(coverage,dict):raise ValueError('coverage must be a story/criterion mapping')
        for id,count in stories.items():
            mapping=coverage.get(id,{})
            if not isinstance(mapping,dict):errors.append(id+': invalid coverage mapping');continue
            for number in range(1,count+1):
                targets=mapping.get(str(number))
                if not isinstance(targets,list) or not targets or any(t not in docs for t in targets):errors.append(f'{id} criterion {number}: missing valid document coverage')
            if not count:errors.append(id+': no acceptance criteria found')
            if set(mapping)-{str(n) for n in range(1,count+1)}:errors.append(id+': coverage references nonexistent criteria')
        if set(coverage)-set(stories):errors.append('Coverage references unknown story IDs')
        for id,item in plan['optional'].items():
            for ref in item.get('requirements',[]):
                if ref.startswith('US-') and ref not in stories:errors.append(id+': unknown triggering story '+ref)
        review=plan.get('review',{})
        if not isinstance(review,dict) or review.get('status')!='reviewed' or any(not meaningful(review.get(k)) for k in ('story_coverage','consistency','diagram','evidence')):
            errors.append('Document consistency/coverage/diagram review is incomplete')
        from validate_contracts import validate
        errors.extend(validate(folder))
        findings=review.get('findings',[]) if isinstance(review,dict) else []
        if not isinstance(findings,list):errors.append('Review findings must be a list')
        else:
            for finding in findings:
                if not isinstance(finding,dict):errors.append('Invalid review finding');continue
                if (finding.get('severity') in ('critical','blocking') or finding.get('blocking') is True) and finding.get('status')!='resolved':errors.append('Unresolved critical/blocking review finding')
    except (OSError,ValueError,KeyError,TypeError) as exc:errors.append('Document plan: '+str(exc))
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    cmd=sub.add_parser('plan');cmd.add_argument('--profiles',nargs='+',required=True)
    cmd=sub.add_parser('scaffold');cmd.add_argument('--project',type=Path,required=True);cmd.add_argument('--plan',type=Path,required=True)
    cmd=sub.add_parser('validate');cmd.add_argument('--project',type=Path,required=True)
    args=p.parse_args()
    try:
        if args.command=='plan':result=make_plan(args.profiles)
        elif args.command=='scaffold':result=scaffold(args.project,json.loads(args.plan.read_text()))
        else:
            result=validate_documents(args.project/'docs/technical-architecture',args.project)
            print(json.dumps(result,indent=2));return bool(result)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print('ERROR: '+str(exc),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
