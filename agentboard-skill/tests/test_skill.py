"""Offline regression tests: python3 -m unittest discover -s tests -v"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scaffold_module = load_module("scaffold_project", ROOT / "scripts/scaffold_project.py")
validator_module = load_module("validate_project", ROOT / "scripts/validate_project.py")
skill_module = load_module("validate_skill", ROOT / "scripts/validate_skill.py")


class AgentBuildTests(unittest.TestCase):
    def test_vision_format(self):
        valid = "## Product Overview\n\nOne paragraph.\n\n## PainPoints\n\n- A problem.\n\n## Features & Value Proposition\n\n**Projects**\n\n- Keep context together.\n"
        self.assertEqual(validator_module.validate_vision_format(valid), [])
        for invalid in (
            valid.replace("One paragraph.", "First paragraph.\n\nSecond paragraph."),
            valid.replace("- A problem.", "A problem."),
            valid.replace("**Projects**\n\n- Keep context together.", "| Feature | Value |\n| --- | --- |\n| Projects | Context |"),
            valid + "\n## Goals\n\nExtra section.\n",
            valid.replace("- Keep context together.", "Keep context together."),
        ):
            with self.subTest(invalid=invalid):
                self.assertTrue(validator_module.validate_vision_format(invalid))

    def test_story_format(self):
        valid = "### US-001 — Create project\n\n- **Story:**\n  - As a builder, I want a project so that I can organize work.\n- **Acceptance Criteria:**\n  - Saving a named project adds it to the list.\n- **Associated Features:**\n  - Project management\n"
        features = {"Project management"}
        self.assertEqual(validator_module.validate_stories_format(valid, features), [])
        for invalid in (
            valid.replace("- **Story:**", "- **Priority:**"),
            valid.replace("  - Saving a named project adds it to the list.", "  Saving a named project adds it to the list."),
            valid.replace("  - Project management", "  - Invented feature"),
            "## MVP Story Index\n\n" + valid,
            valid + "\n- **Dependencies:**\n  - None\n",
        ):
            with self.subTest(invalid=invalid):
                self.assertTrue(validator_module.validate_stories_format(invalid, features))

    def test_skill_bundle_valid(self):
        self.assertEqual(skill_module.validate(), [])

    def test_first_run_without_confirmation_never_creates_files(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "no-projects-dir"
            with self.assertRaises(PermissionError):
                scaffold_module.scaffold("Demo Product", root)
            self.assertFalse(root.exists(), "Fallback must not create even the projects root")

    def test_cli_unconfirmed_returns_error_and_does_not_write(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch) / "projects"
            run = subprocess.run([
                sys.executable, str(ROOT / "scripts/scaffold_project.py"),
                "--name", "Demo Product", "--root", str(root),
            ], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("user approval", run.stderr)
            self.assertFalse(root.exists())

    def test_approved_local_setup_is_idempotent(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, created = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            self.assertTrue(created)
            manifest_path = project / "project-manifest.json"
            first_bytes = manifest_path.read_bytes()
            again, created_again = scaffold_module.scaffold("Demo Product", Path(scratch))
            self.assertEqual(again, project)
            self.assertFalse(created_again)
            self.assertEqual(manifest_path.read_bytes(), first_bytes)
            self.assertEqual(len(list((project / "agents").glob("*.md"))), 6)
            self.assertTrue((project / "docs").is_dir())

    def test_confirmed_project_manifest_is_valid(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            self.assertEqual(validator_module.inspect_project(project), ([], []))
            info = json.loads((project / "project-manifest.json").read_text())["project"]
            self.assertTrue(info["local_storage_confirmed"])
            self.assertTrue(info["local_storage_confirmed_at"])
            self.assertEqual(info["sync_state"], "local_only")
            self.assertIsNone(info["agentboard_project_id"])

    def test_existing_unconfirmed_project_cannot_be_mutated(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            charter = project / "agents/product-manager.md"
            charter.write_text("Custom PM charter", encoding="utf-8")
            manifest = project / "project-manifest.json"
            data = json.loads(manifest.read_text())
            data["project"].pop("local_storage_confirmed", None)
            data["project"].pop("local_storage_confirmed_at", None)
            manifest.write_text(json.dumps(data))
            before = manifest.read_bytes()
            with self.assertRaises(PermissionError):
                scaffold_module.scaffold("Demo Product", Path(scratch))
            self.assertEqual(manifest.read_bytes(), before)
            self.assertEqual(charter.read_text(encoding="utf-8"), "Custom PM charter")
            _, created = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            self.assertFalse(created)
            self.assertTrue(json.loads(manifest.read_text())["project"]["local_storage_confirmed"])
            self.assertEqual(charter.read_text(encoding="utf-8"), "Custom PM charter")

    def test_document_saver_rejects_unapproved_local_project(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            manifest = project / "project-manifest.json"
            data = json.loads(manifest.read_text())
            data["project"]["local_storage_confirmed"] = False
            manifest.write_text(json.dumps(data))
            source = Path(scratch) / "draft.md"
            source.write_text("# Product Vision\nValid draft content", encoding="utf-8")
            run = subprocess.run([
                sys.executable, str(ROOT / "scripts/save_artifact.py"),
                "--project", str(project), "--artifact", "vision", "--source", str(source),
            ], capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("not authorized", run.stderr)
            self.assertFalse((project / "docs/product-vision.md").exists())

    def test_document_save_and_revision_preserve_history(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            source = Path(scratch) / "draft.md"
            command = [sys.executable, str(ROOT / "scripts/save_artifact.py"),
                       "--project", str(project), "--artifact", "vision", "--source", str(source)]
            source.write_text("# Vision\nFirst draft", encoding="utf-8")
            one = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(one.returncode, 0, one.stderr)
            source.write_text("# Vision\nRevised draft", encoding="utf-8")
            without_revise = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(without_revise.returncode, 0)
            with_revise = subprocess.run(command + ["--revise"], capture_output=True, text=True)
            self.assertEqual(with_revise.returncode, 0, with_revise.stderr)
            self.assertEqual((project / "history/vision/0.1.0.md").read_text(), "# Vision\nFirst draft")
            info = json.loads((project / "project-manifest.json").read_text())
            self.assertEqual(info["artifacts"]["vision"]["version"], "0.1.1")

    def test_document_revision_rejects_symlinked_history_parent(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            source = Path(scratch) / "draft.md"
            source.write_text("# Vision\nFirst draft", encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/save_artifact.py"),
                       "--project", str(project), "--artifact", "vision", "--source", str(source)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)

            outside_history = Path(scratch) / "outside-history"
            outside_history.mkdir()
            (project / "history").symlink_to(outside_history, target_is_directory=True)
            source.write_text("# Vision\nRevised draft", encoding="utf-8")
            revised = subprocess.run(command + ["--revise"], capture_output=True, text=True)

            self.assertNotEqual(revised.returncode, 0)
            self.assertFalse((outside_history / "vision/0.1.0.md").exists())

    def test_document_revision_rejects_dangling_archive_symlink(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            source = Path(scratch) / "draft.md"
            source.write_text("# Vision\nFirst draft", encoding="utf-8")
            command = [sys.executable, str(ROOT / "scripts/save_artifact.py"),
                       "--project", str(project), "--artifact", "vision", "--source", str(source)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)

            outside_archive = Path(scratch) / "outside-archive.md"
            archive = project / "history/vision/0.1.0.md"
            archive.parent.mkdir(parents=True)
            archive.symlink_to(outside_archive)
            source.write_text("# Vision\nRevised draft", encoding="utf-8")
            revised = subprocess.run(command + ["--revise"], capture_output=True, text=True)

            self.assertNotEqual(revised.returncode, 0)
            self.assertFalse(outside_archive.exists())

    def test_draft_without_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            manifest = project / "project-manifest.json"
            data = json.loads(manifest.read_text())
            data["artifacts"]["vision"].update(state="draft", version="0.1.0")
            manifest.write_text(json.dumps(data))
            errors, _ = validator_module.inspect_project(project)
            self.assertTrue(any("local file missing" in issue for issue in errors))

    def test_approved_template_is_rejected(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, _ = scaffold_module.scaffold("Demo Product", Path(scratch), user_approved_local=True)
            (project / "docs/product-vision.md").write_text(
                (ROOT / "assets/templates/product-vision.md").read_text(encoding="utf-8"), encoding="utf-8")
            manifest = project / "project-manifest.json"
            data = json.loads(manifest.read_text())
            data["artifacts"]["vision"].update(state="approved", version="1.0.0")
            manifest.write_text(json.dumps(data))
            errors, _ = validator_module.inspect_project(project)
            self.assertTrue(any("unresolved template placeholders" in issue for issue in errors))

    def test_non_ascii_project_name(self):
        with tempfile.TemporaryDirectory() as scratch:
            project, created = scaffold_module.scaffold("繁體中文專案", Path(scratch), user_approved_local=True)
            self.assertTrue(created)
            self.assertTrue(project.name.startswith("project-"))
            self.assertEqual(json.loads((project / "project-manifest.json").read_text())["project"]["name"],
                             "繁體中文專案")


if __name__ == "__main__":
    unittest.main()
