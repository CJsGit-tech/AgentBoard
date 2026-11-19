from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_tickets import validate

class TicketChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name); self.folder=self.project/'docs/tickets'; self.folder.mkdir(parents=True)
        self.ticket=self.folder/'T-001-investigate-input.md'
        self.ticket.write_text('''# T-001 — Investigate lost input

Role: FE
Type: BUG
Status: Open
Verification: Reported
Assignment: Provisional
Depends on: None
Estimate (days): 0.5
Estimate scope: Investigation
Estimate basis: Provisional investigation only; repair is not yet estimated.

## Outcome
Understand and resolve reported lost input.

## Acceptance Criteria
- Investigate; repair if confirmed and verify the repair.

## Context
No related specification is available yet.

## User Report
User in this conversation: saving sometimes loses my input.
''')
        (self.folder/'README.md').write_text('[T-001](T-001-investigate-input.md)\n')
    def test_simple_report_needs_no_reproduction_or_diagnosis(self):
        self.assertEqual(validate(self.project),[])
    def test_rejects_invalid_routing_and_work_type(self):
        self.ticket.write_text(self.ticket.read_text().replace('Role: FE','Role: BOTH').replace('Type: BUG','Type: UPDATE'))
        issues=validate(self.project)
        self.assertTrue(any('invalid Role' in x for x in issues));self.assertTrue(any('invalid Type' in x for x in issues))
    def test_duplicate_ids_and_unindexed_files(self):
        (self.folder/'T-001-another-report.md').write_text(self.ticket.read_text())
        issues=validate(self.project)
        self.assertTrue(any('duplicate ID' in x for x in issues));self.assertTrue(any('unindexed' in x for x in issues))
    def test_dependency_must_exist_and_be_acyclic(self):
        text=self.ticket.read_text();self.ticket.write_text(text.replace('Depends on: None','Depends on: T-999'))
        self.assertTrue(any('unknown dependency' in x for x in validate(self.project)))
        self.ticket.write_text(text.replace('Depends on: None','Depends on: T-001'))
        self.assertTrue(any('cycle' in x for x in validate(self.project)))
    def test_local_context_links_must_resolve(self):
        self.ticket.write_text(self.ticket.read_text()+'\n[Story](../missing.md)\n')
        self.assertTrue(any('broken/unsafe link' in x for x in validate(self.project)))
    def test_done_requires_resolution_and_evidence(self):
        self.ticket.write_text(self.ticket.read_text().replace('Status: Open','Status: Done'))
        issues=validate(self.project)
        self.assertTrue(any('Completion Evidence' in x for x in issues));self.assertTrue(any('unresolved BUG' in x for x in issues))
    def test_build_has_no_bug_report_requirement(self):
        text=self.ticket.read_text().split('## User Report')[0].replace('Type: BUG','Type: BUILD').replace('Verification: Reported','Verification: Not applicable').replace('Estimate scope: Investigation','Estimate scope: Build')
        self.ticket.write_text(text);self.assertEqual(validate(self.project),[])
    def test_unrecognized_verification_is_rejected(self):
        self.ticket.write_text(self.ticket.read_text().replace('Verification: Reported','Verification: Unknown'))
        self.assertTrue(any('invalid Verification' in x for x in validate(self.project)))

    def test_output_gate_checks_tickets_without_mutating_project(self):
        from scaffold_project import scaffold
        from check_outputs import check
        with tempfile.TemporaryDirectory() as temp:
            project,_=scaffold('Demo',Path(temp),user_approved_local=True)
            folder=project/'docs/tickets'; folder.mkdir(parents=True)
            (folder/'README.md').write_text('Ticket index without any tickets.\n')
            before={str(f.relative_to(project)):f.read_bytes() for f in project.rglob('*') if f.is_file()}
            result=check(project,strict=True)
            self.assertFalse(result['valid'])
            self.assertTrue(any('no ticket files' in x for x in result['errors']))
            after={str(f.relative_to(project)):f.read_bytes() for f in project.rglob('*') if f.is_file()}
            self.assertEqual(before,after)

    def test_estimates_reject_missing_zero_negative_and_non_numeric(self):
        original=self.ticket.read_text()
        for value in ['', '0', '-1', 'NaN', 'two', '1-3', '0.00']:
            with self.subTest(value=value):
                self.ticket.write_text(original.replace('Estimate (days): 0.5','Estimate (days): '+value))
                self.assertTrue(any('Estimate (days)' in x for x in validate(self.project)))
        self.ticket.write_text(original.replace('Estimate basis: Provisional investigation only; repair is not yet estimated.\n',''))
        self.assertTrue(any('Estimate basis' in x for x in validate(self.project)))

    def test_reported_bug_cannot_claim_repair_estimate(self):
        self.ticket.write_text(self.ticket.read_text().replace('Estimate scope: Investigation','Estimate scope: Repair'))
        self.assertTrue(any('unverified BUG' in x for x in validate(self.project)))

    def test_confirmed_bug_can_estimate_repair(self):
        self.ticket.write_text(self.ticket.read_text().replace('Verification: Reported','Verification: Confirmed').replace('Estimate scope: Investigation','Estimate scope: Repair'))
        self.assertEqual(validate(self.project),[])
