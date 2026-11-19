#!/usr/bin/env python3
"""Validate local design contracts and JSON examples with standard validators.

Only local JSON references inside technical-architecture are allowed. These are
static design checks, not runtime interoperability or database constraint tests.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from urllib.parse import unquote,urlsplit


def validate(folder):
    root=Path(folder).resolve();errors=[];cache={};registered=set();ref_seen=set()
    def local(relative):
        if not isinstance(relative,str):raise ValueError('Contract path must be a string')
        pathpart=relative.split('#',1)[0]
        parts=Path(pathpart)
        if parts.is_absolute() or '\\' in pathpart or '..' in parts.parts or urlsplit(pathpart).scheme:
            raise ValueError('Unsafe/remote contract path: '+relative)
        p=root/pathpart
        for parent in (p,*p.parents):
            if parent==root.parent:break
            if parent.is_symlink():raise ValueError('Contract symlink not allowed: '+relative)
        if not p.resolve().is_relative_to(root):raise ValueError('Escaping contract path')
        return p
    def unique_object(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:raise ValueError('Duplicate JSON key: '+key)
            obj[key]=value
        return obj
    def load(relative):
        file=local(relative)
        key=str(file.resolve())
        if key not in cache:cache[key]=json.loads(file.read_text(encoding='utf-8'),object_pairs_hook=unique_object)
        return cache[key],file
    def pointer(document,fragment):
        if not fragment:return document
        if not fragment.startswith('/'):raise ValueError('Only local JSON Pointer fragments are supported')
        value=document
        for part in fragment[1:].split('/'):
            part=unquote(part).replace('~1','/').replace('~0','~')
            value=value[int(part)] if isinstance(value,list) else value[part]
        return value
    def resolve_ref(base,reference):
        uri=urlsplit(reference)
        if uri.scheme or uri.netloc:raise ValueError('Remote references are not allowed: '+reference)
        target=(base.parent/unquote(uri.path)).resolve() if uri.path else base.resolve()
        if not target.is_relative_to(root):raise ValueError('Reference escapes contract folder')
        relative=str(target.relative_to(root));doc,file=load(relative)
        return pointer(doc,unquote(uri.fragment)),file
    def walk_refs(value,base):
        if isinstance(value,dict):
            if '$id' in value and urlsplit(value['$id']).scheme:raise ValueError('Absolute schema IDs unsupported; keep references local')
            if '$dynamicRef' in value:raise ValueError('Dynamic references unsupported by this offline contract inventory')
            if '$ref' in value:
                key=(str(base),value['$ref'])
                if key not in ref_seen:
                    ref_seen.add(key);target,targetfile=resolve_ref(base,value['$ref']);walk_refs(target,targetfile)
            for key,child in value.items():
                if key!='$ref':walk_refs(child,base)
        elif isinstance(value,list):
            for child in value:walk_refs(child,base)
    def schema_node(schema,base,seen=None):
        seen=set() if seen is None else seen
        if schema is False:return True
        if not isinstance(schema,dict) or not schema:return False
        if '$ref' in schema:
            key=(str(base),schema['$ref'])
            if key in seen:return False
            seen.add(key);target,file=resolve_ref(base,schema['$ref'])
            if not schema_node(target,file,seen):return False
        assertions={'type','const','enum','properties','required','items','minItems','maxItems','pattern','minLength','maxLength','minimum','maximum','additionalProperties','unevaluatedProperties'}
        if assertions.intersection(schema):return True
        if '$ref' in schema:return True
        for key in ('allOf','anyOf','oneOf'):
            if key in schema and isinstance(schema[key],list) and schema[key]:
                return all(schema_node(child,base,set(seen)) for child in schema[key])
        return False

    try:
        manifest,_=load('contracts/manifest.json');registered.add('contracts/manifest.json')
        if manifest.get('schema_version')!=1 or manifest.get('status')!='draft':raise ValueError('Contracts manifest must be a completed draft, not a skeleton')
        scopes=manifest.get('scope',{})
        for name in ('rest','mcp','data'):
            item=scopes.get(name,{})
            if type(item.get('applicable')) is not bool or not isinstance(item.get('reason'),str) or not item['reason'].strip() or re.search(r'TODO|TBD|SKELETON|\[WRITE:',item['reason'],re.I):raise ValueError('Unfinished contract scope: '+name)
        schemas=manifest.get('schemas',[]);examples=manifest.get('examples',[])
        if not isinstance(schemas,list) or len(schemas)!=len(set(schemas)) or not isinstance(examples,list):raise ValueError('Invalid contract inventory')
        needs_validation=bool(schemas or examples or scopes['rest']['applicable'] or scopes['mcp']['applicable'])
        if needs_validation:
            try:
                from jsonschema import Draft202012Validator,FormatChecker
                from referencing import Registry,Resource
                from referencing.jsonschema import DRAFT202012
            except ImportError:return ['Contract validation requires requirements-contracts.txt; use the configured contract virtual environment']
            def retrieve(uri):
                parsed=urlsplit(uri)
                if parsed.scheme!='file' or parsed.netloc:raise ValueError('Remote schema retrieval disabled')
                path=Path(unquote(parsed.path)).resolve()
                if not path.is_relative_to(root):raise ValueError('Schema retrieval escapes root')
                doc,_=load(str(path.relative_to(root)))
                return Resource.from_contents(doc,default_specification=DRAFT202012)
            registry=Registry(retrieve=retrieve)
            for relative in schemas:
                if not relative.startswith('contracts/') or not relative.endswith('.schema.json'):raise ValueError('Schema inventory must contain contracts/*.schema.json')
                schema,file=load(relative);registered.add(relative);walk_refs(schema,file);Draft202012Validator.check_schema(schema)
        spec=None;specfile=None;operations={};tools={};catalogfile=None
        if scopes['rest']['applicable']:
            path=manifest.get('openapi')
            if not path:raise ValueError('REST scope needs an OpenAPI contract')
            spec,specfile=load(path);registered.add(path);walk_refs(spec,specfile)
            try:from openapi_spec_validator import OpenAPIV31SpecValidator
            except ImportError:return ['OpenAPI validation requires requirements-contracts.txt']
            if not str(spec.get('openapi','')).startswith('3.1.'):raise ValueError('This validator supports OpenAPI 3.1 JSON contracts')
            errors.extend('OpenAPI: '+str(e) for e in OpenAPIV31SpecValidator(spec,base_uri=specfile.as_uri()).iter_errors())
            for path,item in spec.get('paths',{}).items():
                for method,operation in item.items():
                    if method not in ('get','post','patch','put','delete','head','options'):continue
                    id=operation.get('operationId')
                    if not id or id in operations:raise ValueError('Missing/duplicate OpenAPI operationId')
                    operations[id]=operation
        elif manifest.get('openapi'):raise ValueError('OpenAPI present while REST marked not applicable')
        if scopes['mcp']['applicable']:
            path=manifest.get('mcp_catalog')
            if not path:raise ValueError('MCP scope needs a tool catalog')
            catalog,catalogfile=load(path);registered.add(path);walk_refs(catalog,catalogfile)
            for tool in catalog.get('tools',[]):
                name=tool.get('name')
                if not name or name in tools:raise ValueError('Missing/duplicate MCP tool name')
                if tool.get('x-agentbuild-permission') not in ('read','create','approval_required'):raise ValueError(name+': missing permission contract')
                for field in ('inputSchema','outputSchema'):
                    if not isinstance(tool.get(field),dict):raise ValueError(name+': missing '+field)
                    Draft202012Validator.check_schema(tool[field])
                hint=tool.get('annotations',{}).get('readOnlyHint')
                if 'readOnlyHint' in tool.get('annotations',{}) and (type(hint) is not bool or hint != (tool['x-agentbuild-permission']=='read')):
                    errors.append(name+': readOnlyHint conflicts with declared permission')
                required=tool.get('x-agentbuild-required-outcomes',[])
                if not isinstance(required,list) or any(not isinstance(x,str) or not x for x in required) or len(required)!=len(set(required)):
                    raise ValueError(name+': invalid required outcome coverage')
                tools[name]=tool
            if not tools:raise ValueError('MCP scope declares no tools')
        elif manifest.get('mcp_catalog'):raise ValueError('MCP catalog present while MCP marked not applicable')
        seen_bindings=set();kinds=set();outcomes={};rest_bindings=set();example_entries=set()
        for example in examples:
            signature=json.dumps(example,sort_keys=True)
            if signature in example_entries:raise ValueError('Duplicate example binding')
            example_entries.add(signature)
            relative=example['path']
            if not relative.startswith('examples/') or not relative.endswith('.json'):raise ValueError('Examples must live under examples/')
            instance,examplefile=load(relative);registered.add(relative);kind=example['kind'];kinds.add(kind)
            if kind=='data':
                if not scopes['data']['applicable']:raise ValueError('Data examples conflict with not-applicable data scope')
                target=example['schema'];docpath,_,fragment=target.partition('#')
                if docpath not in schemas:raise ValueError('Data example must bind to an inventoried schema file')
                schema,base=load(docpath)
                schema=pointer(schema,fragment)
            elif kind in ('mcp-input','mcp-output'):
                name=example['tool']
                if name not in tools:raise ValueError('Example references unknown MCP tool')
                schema=tools[name]['inputSchema' if kind=='mcp-input' else 'outputSchema'];base=catalogfile
                seen_bindings.add((name,kind))
                if kind=='mcp-output' and isinstance(instance,dict) and isinstance(instance.get('outcome'),str):outcomes.setdefault(name,set()).add(instance['outcome'])
            elif kind in ('rest-request','rest-response'):
                id=example['operation_id']
                if id not in operations:raise ValueError('Example references unknown REST operation')
                op=operations[id];base=specfile
                rest_bindings.add((id,kind,str(example.get('status',''))))
                if kind=='rest-request':schema=op['requestBody']['content']['application/json']['schema']
                else:schema=op['responses'][str(example['status'])]['content']['application/json']['schema']
            else:raise ValueError('Unknown example kind: '+kind)
            if not isinstance(schema,(dict,bool)) or not schema_node(schema,base):raise ValueError('Example target is not a schema-bearing node')
            walk_refs(schema,base);Draft202012Validator.check_schema(schema)
            # A dedicated synthetic resource retains the containing document base;
            # local fragments must point at the actual document, not the wrapper.
            def absolutize(value):
                if isinstance(value,dict):
                    out={k:absolutize(v) for k,v in value.items()}
                    if '$ref' in out:
                        raw=out['$ref'];uri=urlsplit(raw)
                        if uri.scheme or uri.netloc:raise ValueError('Remote example schema ref')
                        file=(base.parent/unquote(uri.path)).resolve() if uri.path else base.resolve()
                        out['$ref']=file.as_uri()+('#'+uri.fragment if uri.fragment else '')
                    return out
                if isinstance(value,list):return [absolutize(v) for v in value]
                return value
            validator=Draft202012Validator(absolutize(schema),registry=registry,format_checker=FormatChecker())
            errors.extend('Invalid example '+relative+': '+e.message for e in validator.iter_errors(instance))
        for id,op in operations.items():
            required=op.get('x-agentbuild-required-examples',{})
            if not isinstance(required,dict) or type(required.get('request',False)) is not bool or not isinstance(required.get('responses',[]),list):raise ValueError('Invalid REST example coverage declaration: '+id)
            if required.get('request') and (id,'rest-request','') not in rest_bindings:errors.append(id+': missing required request example')
            for status in required.get('responses',[]):
                if not isinstance(status,str) or status not in op['responses']:raise ValueError(id+': required example status is not declared by the operation')
                if (id,'rest-response',status) not in rest_bindings:errors.append(id+': missing required response example '+status)
        if scopes['data']['applicable'] and 'data' not in kinds:errors.append('Data scope needs representative record examples')
        if scopes['rest']['applicable'] and not {'rest-request','rest-response'}<=kinds:errors.append('REST scope needs request and response examples')
        if scopes['mcp']['applicable']:
            for name in tools:
                for outcome in tools[name].get('x-agentbuild-required-outcomes',[]):
                    if outcome not in outcomes.get(name,set()):errors.append(name+': missing required outcome example '+outcome)
                for kind in ('mcp-input','mcp-output'):
                    if (name,kind) not in seen_bindings:errors.append(name+': missing '+kind+' example')
        for directory in ('contracts','examples'):
            for file in (root/directory).rglob('*'):
                if file.is_symlink():raise ValueError('Contract/example symlink not allowed')
                if file.is_file() and file.suffix=='.md' and re.search(r'AGENTBUILD:SKELETON|\[WRITE:',file.read_text(),re.I):errors.append('Unfinished contract/example guidance: '+str(file.relative_to(root)))
                if file.is_file() and file.suffix=='.json' and str(file.relative_to(root)) not in registered:
                    errors.append('Unregistered JSON contract/example: '+str(file.relative_to(root)))
    except Exception as exc:
        errors.append('Contract validation: '+str(exc))
    return errors


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);args=p.parse_args()
    errors=validate(args.project/'docs/technical-architecture')
    for error in errors:print('ERROR: '+error)
    print('Contract/example validation: '+str(len(errors))+' error(s)')
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
