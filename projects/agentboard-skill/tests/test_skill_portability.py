from pathlib import Path
import json,os,tempfile,unittest,sys
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_screen_evidence import context_fingerprint,guidance_skill_path
from validate_skill import validate

class FreshnessTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name).resolve()
  (self.p/'docs').mkdir();(self.p/'agents').mkdir()
  (self.p/'docs/product-vision.md').write_text('> Owner: PM | Version: 0.1.0 | Status: draft | Last Updated: 2026-01-01\n\n## Product Overview\nReal scope.\n')
  self.manifest=self.p/'project-manifest.json'
  self.data={'project':{'name':'Demo','storage_mode':'local','updated_at':'first'},'artifacts':{'vision':{'path':'docs/product-vision.md','version':'0.1.0','state':'draft'}},'open_decisions':[]}
  self.save()
 def save(self):self.manifest.write_text(json.dumps(self.data))
 def test_timestamp_and_version_do_not_invalidate(self):
  before=context_fingerprint(self.p);self.data['project']['updated_at']='later';self.data['artifacts']['vision']['version']='0.1.1';self.save()
  f=self.p/'docs/product-vision.md';f.write_text(f.read_text().replace('0.1.0','0.1.1').replace('2026-01-01','2026-02-01'))
  self.assertEqual(context_fingerprint(self.p),before)
 def test_real_requirement_invalidates(self):
  before=context_fingerprint(self.p);f=self.p/'docs/product-vision.md';f.write_text(f.read_text().replace('Real scope.','A new required screen.'));self.assertNotEqual(context_fingerprint(self.p),before)
 def test_semantic_manifest_configuration_invalidates(self):
  before=context_fingerprint(self.p);self.data['project']['target_platform']='ios';self.save();self.assertNotEqual(context_fingerprint(self.p),before)
 def test_review_outputs_do_not_invalidate(self):
  before=context_fingerprint(self.p);(self.p/'docs/review-report.md').write_text('Review findings only.');self.assertEqual(context_fingerprint(self.p),before)
 def test_ticket_progress_preserved_but_new_scope_invalidates(self):
  folder=self.p/'docs/tickets';folder.mkdir();t=folder/'T-001-build.md';t.write_text('# T-001 — Build\n\nStatus: Open\nEstimate (days): 1\n\n## Outcome\nBuild existing feature.\n\n## Acceptance Criteria\n- Persist data.\n')
  before=context_fingerprint(self.p);t.write_text(t.read_text().replace('Status: Open','Status: In progress').replace('Estimate (days): 1','Estimate (days): 2')+'\n## Investigation\nAttempted checks.\n')
  self.assertEqual(context_fingerprint(self.p),before)
  t.write_text(t.read_text().replace('Persist data.','Add timeline UI.'));self.assertNotEqual(context_fingerprint(self.p),before)
 def test_symlink_requirement_is_rejected(self):
  target=self.p/'real.md';target.write_text('scope');(self.p/'docs/linked.md').symlink_to(target)
  with self.assertRaises(ValueError):context_fingerprint(self.p)

 def test_approval_metadata_and_remote_ids_do_not_invalidate(self):
  before=context_fingerprint(self.p)
  self.data['artifacts']['vision'].update(state='approved',agentboard_document_id='remote-doc')
  self.data['project'].update(agentboard_project_id='remote-project',sync_state='synced')
  self.save();f=self.p/'docs/product-vision.md';f.write_text(f.read_text().replace('Status: draft','Status: approved'))
  self.assertEqual(context_fingerprint(self.p),before)
 def test_role_path_is_semantic_but_remote_role_state_is_not(self):
  self.data['agents']={'frontend':{'local_role_path':'agents/frontend.md','state':'defined_locally','agentboard_agent_id':None}};self.save()
  before=context_fingerprint(self.p);self.data['agents']['frontend'].update(state='registered',agentboard_agent_id='remote');self.save()
  self.assertEqual(context_fingerprint(self.p),before)
  self.data['agents']['frontend']['local_role_path']='agents/other.md';self.save();self.assertNotEqual(context_fingerprint(self.p),before)
 def test_ticket_body_metadata_words_are_requirements(self):
  folder=self.p/'docs/tickets';folder.mkdir();t=folder/'T-001-build.md';t.write_text('# T-001 — Build\n\nStatus: Open\n\n## Outcome\nInspect status.\n\n## User Report\nStatus: does not persist\n')
  before=context_fingerprint(self.p);t.write_text(t.read_text().replace('Status: does not persist','Status: persists incorrectly'))
  self.assertNotEqual(context_fingerprint(self.p),before)
 def test_ticket_index_preserves_policy_but_ignores_inventory(self):
  folder=self.p/'docs/tickets';folder.mkdir();t=folder/'README.md'
  t.write_text('Planning policy: eight hours per day.\n\n| ID | Role | Type | Status | Verification |\n| --- | --- | --- | --- | --- |\n| T-001 | FE | BUILD | Open | Not applicable |\n')
  before=context_fingerprint(self.p);t.write_text(t.read_text().replace('BUILD | Open','BUILD | Done'))
  self.assertEqual(context_fingerprint(self.p),before)
  t.write_text(t.read_text().replace('eight hours','six hours'));self.assertNotEqual(context_fingerprint(self.p),before)
 def test_other_screen_named_requirements_remain_binding(self):
  before=context_fingerprint(self.p);f=self.p/'docs/features/screens/requirements.md';f.parent.mkdir(parents=True);f.write_text('Required screen.')
  self.assertNotEqual(context_fingerprint(self.p),before)

 def test_plain_document_metadata_is_bookkeeping(self):
  f=self.p/'docs/plain.md';f.write_text('# Specification\n\nOwner: Designer\nVersion: 1\nStatus: draft\nLast Updated: 2026-01-01\n\n## Requirements\nStatus: must remain visible.\n')
  before=context_fingerprint(self.p);f.write_text(f.read_text().replace('Version: 1','Version: 2').replace('Status: draft','Status: approved').replace('2026-01-01','2026-02-01'))
  self.assertEqual(context_fingerprint(self.p),before)
  f.write_text(f.read_text().replace('Status: must remain visible.','Status: must show blockers.'));self.assertNotEqual(context_fingerprint(self.p),before)

 def test_quoted_body_metadata_remains_binding(self):
  f=self.p/'docs/report.md';f.write_text('# Specification\n\n> Owner: PM | Status: draft | Version: 1\n\n## User Report\n> Owner: UI | Status: missing input\n')
  before=context_fingerprint(self.p);f.write_text(f.read_text().replace('Status: missing input','Status: incorrect input'));self.assertNotEqual(context_fingerprint(self.p),before)
 def test_alias_ticket_table_columns_are_inventory(self):
  folder=self.p/'docs/tickets';folder.mkdir();f=folder/'README.md';f.write_text('| ID | FE/BE | BUG/BUILD | Status | Verification |\n| --- | --- | --- | --- | --- |\n| T-001 | FE | BUILD | Open | Not applicable |\n')
  before=context_fingerprint(self.p);f.write_text(f.read_text().replace('BUILD | Open','BUILD | Done'));self.assertEqual(context_fingerprint(self.p),before)

class GuidanceDiscoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.p=Path(self.tmp.name).resolve()
  self.home=self.p/'home';self.home.mkdir();self.project=self.p/'project';self.project.mkdir()
  self.patch=patch('check_screen_evidence.Path.home',return_value=self.home);self.patch.start();self.addCleanup(self.patch.stop)
  self.env=patch.dict(os.environ,{},clear=True);self.env.start();self.addCleanup(self.env.stop)
 def skill(self,path,name='modern-web-guidance'):
  path.parent.mkdir(parents=True,exist_ok=True);path.write_text(f'---\nname: {name}\ndescription: Guidance\n---\nRead me.\n');return path
 def test_claude_user_location(self):
  expected=self.skill(self.home/'.claude/skills/modern-web-guidance/SKILL.md');self.assertEqual(guidance_skill_path(self.project),expected)
 def test_project_ancestor_location(self):
  expected=self.skill(self.project/'.agents/skills/modern-web-guidance/SKILL.md');nested=self.project/'nested';nested.mkdir();self.assertEqual(guidance_skill_path(nested),expected)
 def test_explicit_path_and_invalid_override(self):
  expected=self.skill(self.p/'custom/SKILL.md');self.assertEqual(guidance_skill_path(self.project,explicit=expected),expected)
  self.skill(self.home/'.claude/skills/modern-web-guidance/SKILL.md')
  with self.assertRaisesRegex(ValueError,'override'):guidance_skill_path(self.project,explicit=self.p/'missing')
 def test_invalid_name_is_not_accepted(self):
  self.skill(self.home/'.claude/skills/modern-web-guidance/SKILL.md','unrelated')
  with self.assertRaisesRegex(ValueError,'searched'):guidance_skill_path(self.project)
 def test_codex_home_and_environment_override(self):
  expected=self.skill(self.p/'codex/skills/modern-web-guidance/SKILL.md');os.environ['CODEX_HOME']=str(self.p/'codex');self.assertEqual(guidance_skill_path(self.project),expected)
  override=self.skill(self.p/'override/SKILL.md');os.environ['AGENTBUILD_GUIDANCE_SKILL']=str(override);self.assertEqual(guidance_skill_path(self.project),override)

class ResourceLinkTests(unittest.TestCase):
 def test_broken_entrypoint_reference_fails(self):
  with tempfile.TemporaryDirectory() as tmp:
   import shutil
   root=Path(tmp)/'skill';shutil.copytree(Path(__file__).resolve().parents[1],root,ignore=shutil.ignore_patterns('__pycache__'))
   with (root/'SKILL.md').open('a') as f:f.write('\nSee references/missing-rule.md\n')
   self.assertTrue(any('missing-rule.md' in e for e in validate(root)))
