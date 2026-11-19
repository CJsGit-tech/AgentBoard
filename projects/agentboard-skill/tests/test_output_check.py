from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from scaffold_project import scaffold
from check_outputs import check

class OutputCheckTests(unittest.TestCase):
    def test_read_only_gate_and_machine_report(self):
        with tempfile.TemporaryDirectory() as temp:
            project,_=scaffold('Demo',Path(temp),user_approved_local=True)
            before=(project/'project-manifest.json').read_bytes()
            result=check(project,strict=True)
            self.assertTrue(result['valid']);self.assertEqual(result['counts']['story_files'],0)
            self.assertEqual(before,(project/'project-manifest.json').read_bytes())
            folder=project/'docs/technical-architecture/contracts';folder.mkdir(parents=True)
            (folder/'manifest.json').write_text('{bad json')
            self.assertFalse(check(project)['valid'])
