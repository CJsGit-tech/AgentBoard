from pathlib import Path
import json,tempfile,unittest,sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_screen_evidence import validate,fingerprint,context_fingerprint
class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name)
  for name in ['frontend/src/App.tsx','agents/frontend-programmer.md','agents/code-reviewer.md','review.md','log.txt','capture.png']:
   f=self.p/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text('evidence')
  self.data={'schema_version':1,'status':'verified_pending_review','source_root':'frontend','source_fingerprint':fingerprint(self.p,'frontend'),'builder':{'agent_id':'builder-1','role_file':'agents/frontend-programmer.md'},'reviewer':{'agent_id':'reviewer-1','role_file':'agents/code-reviewer.md','independent':True,'verdict':'pass','source_fingerprint':fingerprint(self.p,'frontend'),'report':'review.md'},'checks':[{'id':k,'kind':k,'status':'pass','exit_code':0,'command':'actual command','cwd':'frontend','finished_at':'2026-11-18T00:00:00Z','log':'log.txt'} for k in ['build','typecheck','ui','output-consistency','legacy-scan']],'screens':[{'id':'tickets','requirements':['US-004'],'status':'verified','source':'frontend/src/App.tsx','captures':['capture.png'],'ui_checks':['ui']}],'unresolved_required_items':[]}
  dep=self.p/'guidance-skill.md';dep.write_text('---\nname: modern-web-guidance\ndescription: Guidance\n---\n')
  self.dep_patch=patch('check_screen_evidence.guidance_skill_path',return_value=dep);self.dep_patch.start();self.addCleanup(self.dep_patch.stop)
  self.data['legacy_scan']={'status':'reviewed','source_fingerprint':fingerprint(self.p,'frontend'),'raw_output':'log.txt','report':'review.md'}
  self.data['context_fingerprint_version']=2
  self.data['target_platform']='web'
  self.data['guidance']={'status':'reviewed','guides':['dialog'],'cli_version':'test','skill_version':'test','report':'review.md'}
  self.data['context_fingerprint']=context_fingerprint(self.p)
  self.data['reviewer']['context_fingerprint']=context_fingerprint(self.p)
 def check(self):
  f=self.p/'docs/designs/screens/evidence/latest.json';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(self.data));return validate(self.p)
 def test_complete(self):self.assertEqual(self.check(),[])
 def test_no_self_review(self):
  self.data['reviewer']['agent_id']='builder-1';self.assertTrue(self.check())
 def test_changed_source(self):
  (self.p/'frontend/src/App.tsx').write_text('changed');self.assertTrue(self.check())
 def test_failed_check(self):
  self.data['checks'][0]['exit_code']=1;self.assertTrue(self.check())
 def test_missing_capture(self):
  (self.p/'capture.png').unlink();self.assertTrue(self.check())
 def test_unresolved(self):
  self.data['unresolved_required_items']=['activity missing'];self.assertTrue(self.check())
 def test_missing_evidence(self):self.assertTrue(validate(self.p))

 def test_missing_check_ids(self):
  self.data['checks'][0].pop('id');self.assertTrue(self.check())
 def test_unfingerprinted_screen(self):
  self.data['screens'][0]['source']='log.txt';self.assertTrue(self.check())
 def test_missing_working_directory(self):
  self.data['checks'][0].pop('cwd');self.assertTrue(self.check())

 def test_changed_requirements(self):
  (self.p/'agents/code-reviewer.md').write_text('new review requirement');self.assertTrue(self.check())

 def test_missing_guidance_review(self):
  self.data.pop('guidance');self.assertTrue(self.check())
 def test_missing_required_dependency(self):
  (self.p/'guidance-skill.md').unlink();self.assertTrue(self.check())

 def test_missing_legacy_scan(self):
  self.data.pop('legacy_scan');self.assertTrue(self.check())
 def test_stale_legacy_scan(self):
  self.data['legacy_scan']['source_fingerprint']='old';self.assertTrue(self.check())

 def test_old_context_policy_needs_review(self):
  self.data.pop('context_fingerprint_version');self.assertTrue(any('policy changed' in x for x in self.check()))

 def test_quoted_guidance_name_passes(self):
  (self.p/'guidance-skill.md').write_text('---\nname: "modern-web-guidance"\ndescription: Guidance\n---\n')
  # Actual identity resolver with an explicit path, not the fixture's patched return.
  self.dep_patch.stop()
  self.assertEqual(validate_with_explicit(self),[])

 def test_context_cli_errors_without_traceback(self):
  import subprocess
  (self.p/'project-manifest.json').write_text('{bad json')
  result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/check_screen_evidence.py'),'--project',str(self.p),'--context-fingerprint'],capture_output=True,text=True)
  self.assertEqual(result.returncode,1);self.assertIn('ERROR:',result.stdout);self.assertNotIn('Traceback',result.stderr)

def validate_with_explicit(case):
 f=case.p/'docs/designs/screens/evidence/latest.json';f.parent.mkdir(parents=True,exist_ok=True);f.write_text(json.dumps(case.data))
 return validate(case.p,case.p/'guidance-skill.md')
