import json
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_contracts as c

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);(self.root/'contracts').mkdir();(self.root/'examples/data').mkdir(parents=True)
        self.schema={'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object','properties':{'id':{'type':'string','format':'uuid'}},'required':['id'],'additionalProperties':False}
        self.write('contracts/record.schema.json',self.schema)
        self.write('examples/data/record.json',{'id':'11111111-1111-4111-8111-111111111111'})
        self.manifest={'schema_version':1,'status':'draft','scope':{'rest':{'applicable':False,'reason':'No HTTP API.'},'mcp':{'applicable':False,'reason':'No MCP integration.'},'data':{'applicable':True,'reason':'Local records.'}},'openapi':None,'mcp_catalog':None,'schemas':['contracts/record.schema.json'],'examples':[{'path':'examples/data/record.json','kind':'data','schema':'contracts/record.schema.json'}]}
        self.save()
    def write(self,path,value):
        file=self.root/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_text(json.dumps(value))
    def save(self):self.write('contracts/manifest.json',self.manifest)
    def test_valid_data_example(self):self.assertEqual(c.validate(self.root),[])
    def test_invalid_uuid_and_extra_field(self):
        self.write('examples/data/record.json',{'id':'ticket-001','status':'unknown'})
        self.assertTrue(any('example' in e.lower() for e in c.validate(self.root)))
    def test_bad_ref_or_unregistered_example_fails(self):
        self.write('contracts/record.schema.json',dict(self.schema,properties={'id':{'$ref':'missing.json'}}))
        self.assertTrue(c.validate(self.root))
        self.write('contracts/record.schema.json',self.schema)
        self.write('examples/data/orphan.json',{})
        self.assertTrue(any('unregistered' in e.lower() for e in c.validate(self.root)))
    def test_network_reference_is_rejected(self):
        self.write('contracts/record.schema.json',{'$ref':'https://example.com/remote-schema.json'})
        self.assertTrue(any('remote' in e.lower() for e in c.validate(self.root)))
    def test_escaping_paths_are_rejected(self):
        self.manifest['examples'][0]['path']='../outside.json';self.save()
        self.assertTrue(c.validate(self.root))
    def test_unfinished_scope_is_not_ready(self):
        self.manifest['scope']['rest']={'applicable':None,'reason':'TODO'};self.save()
        self.assertTrue(c.validate(self.root))
    def test_rest_examples_bind_to_real_operation_schemas(self):
        self.manifest['scope']['rest']={'applicable':True,'reason':'Record API.'}
        self.manifest['openapi']='contracts/openapi.json'
        ref={'$ref':'record.schema.json'}
        self.write('contracts/openapi.json',{'openapi':'3.1.1','info':{'title':'Test','version':'1.0.0'},'paths':{'/records':{'post':{'operationId':'create_record','requestBody':{'required':True,'content':{'application/json':{'schema':ref}}},'responses':{'201':{'description':'Created','content':{'application/json':{'schema':ref}}}}}}}})
        for kind in ('rest-request','rest-response'):
            path='examples/api/'+kind+'.json';self.write(path,{'id':'11111111-1111-4111-8111-111111111111'})
            entry={'path':path,'kind':kind,'operation_id':'create_record'}
            if kind=='rest-response':entry['status']='201'
            self.manifest['examples'].append(entry)
        self.save();self.assertEqual(c.validate(self.root),[])
        self.write('examples/api/rest-request.json',{'id':'not-a-uuid'})
        self.assertTrue(any('Invalid example' in e for e in c.validate(self.root)))

    def test_mcp_outputs_use_the_declared_tool_contract(self):
        self.manifest['scope']['mcp']={'applicable':True,'reason':'Read records.'}
        self.manifest['mcp_catalog']='contracts/mcp/tools.json'
        self.write('contracts/mcp/tools.json',{'tools':[{'name':'read_record','inputSchema':{'type':'object','$ref':'../record.schema.json'},'outputSchema':{'type':'object','$ref':'../record.schema.json'},'x-agentbuild-permission':'read'}]})
        for kind in ('mcp-input','mcp-output'):
            path='examples/mcp/'+kind+'.json';self.write(path,{'id':'11111111-1111-4111-8111-111111111111'})
            self.manifest['examples'].append({'path':path,'kind':kind,'tool':'read_record'})
        self.save();self.assertEqual(c.validate(self.root),[])
        self.write('examples/mcp/mcp-output.json',{'id':'wrong'})
        self.assertTrue(any('Invalid example' in e for e in c.validate(self.root)))

    def test_data_binding_cannot_point_at_metadata_or_definitions_map(self):
        self.write('examples/data/record.json',{'nonsense':True})
        self.manifest['examples'][0]['schema']='contracts/manifest.json';self.save()
        self.assertTrue(c.validate(self.root))
        self.write('contracts/record.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$defs':{'Record':self.schema}})
        self.manifest['examples'][0]['schema']='contracts/record.schema.json#/$defs';self.save()
        self.assertTrue(c.validate(self.root))

    def test_duplicate_json_keys_fail_instead_of_silently_overriding(self):
        (self.root/'contracts/record.schema.json').write_text('{"type":"object","type":"string"}')
        self.assertTrue(any('duplicate' in e.lower() for e in c.validate(self.root)))

    def test_permission_hints_and_required_outcomes_match_examples(self):
        self.manifest['scope']['mcp']={'applicable':True,'reason':'Read records.'};self.manifest['mcp_catalog']='contracts/mcp/tools.json'
        tool={'name':'read_record','inputSchema':{'type':'object','$ref':'../record.schema.json'},'outputSchema':{'type':'object','properties':{'outcome':{'type':'string','enum':['success','error']}},'required':['outcome'],'additionalProperties':False},'x-agentbuild-permission':'read','annotations':{'readOnlyHint':False},'x-agentbuild-required-outcomes':['success','error']}
        self.write('contracts/mcp/tools.json',{'tools':[tool]})
        for kind,value in [('mcp-input',{'id':'11111111-1111-4111-8111-111111111111'}),('mcp-output',{'outcome':'success'})]:
            path='examples/mcp/'+kind+'.json';self.write(path,value);self.manifest['examples'].append({'path':path,'kind':kind,'tool':'read_record'})
        self.save()
        for bad_hint in (False,None,'true',1):
            tool['annotations']['readOnlyHint']=bad_hint;self.write('contracts/mcp/tools.json',{'tools':[tool]})
            self.assertTrue(any('hint' in e.lower() for e in c.validate(self.root)))
        tool['annotations']['readOnlyHint']=True;self.write('contracts/mcp/tools.json',{'tools':[tool]})
        self.assertTrue(any('outcome' in e.lower() for e in c.validate(self.root)))
        self.write('examples/mcp/error.json',{'outcome':'error'});self.manifest['examples'].append({'path':'examples/mcp/error.json','kind':'mcp-output','tool':'read_record'});self.save()
        self.assertEqual(c.validate(self.root),[])

    def test_required_rest_response_examples_cannot_disappear(self):
        self.test_rest_examples_bind_to_real_operation_schemas()
        self.write('examples/api/rest-request.json',{'id':'11111111-1111-4111-8111-111111111111'})
        file=self.root/'contracts/openapi.json';spec=json.loads(file.read_text());op=spec['paths']['/records']['post']
        op['responses']['400']=op['responses']['201'];op['x-agentbuild-required-examples']={'request':True,'responses':['201','400']}
        self.write('contracts/openapi.json',spec)
        self.assertTrue(any('400' in e for e in c.validate(self.root)))

    def test_missing_mcp_examples_are_rejected(self):
        self.manifest['scope']['mcp']={'applicable':True,'reason':'Agent tools.'}
        self.manifest['mcp_catalog']='contracts/mcp/tools.json'
        self.write('contracts/mcp/tools.json',{'tools':[{'name':'read_record','inputSchema':{'type':'object'},'outputSchema':{'type':'object'},'x-agentbuild-permission':'read'}]})
        self.save();self.assertTrue(any('read_record' in e for e in c.validate(self.root)))
