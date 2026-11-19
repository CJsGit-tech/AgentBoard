#!/usr/bin/env python3
"""One read-only consistency gate. Does not certify semantic correctness/runtime."""
import argparse,json
from pathlib import Path
from validate_project import inspect_project
from sync_navigation import sync
from check_tickets import validate as validate_tickets
from validate_metadata import validate as validate_metadata


def check(project,strict=False):
    project=Path(project).expanduser().resolve();errors=[];warnings=[];counts={}
    try:
        errors,warnings=inspect_project(project)
        nav=sync(project)
        errors.extend(nav['errors'])
        errors.extend('Stale navigation: '+path+'; run sync_navigation.py --write' for path in nav['changed'])
        if (project/'docs/tickets').exists() or 'tickets' in json.loads((project/'project-manifest.json').read_text()).get('artifacts', {}):
            errors.extend(validate_tickets(project))
        errors.extend(validate_metadata(project))
        counts['story_files']=len(list((project/'docs/user-stories').glob('US-*.md')))
        root=project/'docs/technical-architecture';manifest_file=root/'contracts/manifest.json'
        if manifest_file.is_file():
            manifest=json.loads(manifest_file.read_text());counts['registered_examples']=len(manifest.get('examples',[]))
            path=manifest.get('mcp_catalog')
            if path and not Path(path).is_absolute() and '..' not in Path(path).parts:
                counts['mcp_tools']=len(json.loads((root/path).read_text()).get('tools',[]))
            path=manifest.get('openapi')
            if path and not Path(path).is_absolute() and '..' not in Path(path).parts:
                spec=json.loads((root/path).read_text())
                counts['rest_operations']=sum(len(set(item)&{'get','post','put','patch','delete','head','options'}) for item in spec.get('paths',{}).values())
    except Exception as exc:errors.append('Output consistency check failed: '+str(exc))
    return {'valid':not errors and (not strict or not warnings),'errors':errors,'warnings':warnings,'counts':counts,
        'scope':'Structural consistency of existing outputs; not proof of semantic review, approval or runtime behavior.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--strict',action='store_true');p.add_argument('--json',action='store_true');a=p.parse_args()
    result=check(a.project,a.strict)
    if a.json:print(json.dumps(result,indent=2))
    else:
        for message in result['errors']:print('ERROR: '+message)
        for message in result['warnings']:print('WARNING: '+message)
        print('Output consistency: '+('PASS' if result['valid'] else 'FAIL'))
        print(json.dumps(result['counts'],sort_keys=True))
        print(result['scope'])
    return not result['valid']


if __name__=='__main__':raise SystemExit(main())
