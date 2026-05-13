import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "agent-harness.js"


def run_cli(*args: str, cwd: Path, home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["HARNESS_SESSION_NOW"] = "2026-05-13T10:11:12+09:00"
    return subprocess.run(
        ["node", str(CLI), *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


class AgentHarnessCliTest(unittest.TestCase):
    def test_setup_project_applies_harness_files_and_managed_instruction_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            compound = root / "compound"
            project.mkdir()
            home.mkdir()

            result = run_cli(
                "setup",
                "--type",
                "project",
                "--project-root",
                str(project),
                "--compound-root",
                str(compound),
                "--workflow",
                "gstack",
                "--instructions",
                "gemini",
                "--yes",
                cwd=project,
                home=home,
            )

            self.assertIn("project harness setup complete", result.stdout)
            self.assertIn("workflow_engine: gstack", (project / ".harness" / "config.yaml").read_text())
            self.assertTrue((project / ".harness" / "sessions").is_dir())
            self.assertTrue((project / ".harness" / ".company-harness-managed.json").is_file())
            self.assertIn("<!-- company-agent-harness:start -->", (project / "GEMINI.md").read_text())

    def test_setup_project_is_idempotent_for_instruction_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            project.mkdir()
            home.mkdir()
            (project / "AGENTS.md").write_text("# Existing\n\nKeep me.\n", encoding="utf-8")

            run_cli("setup", "--type", "project", "--project-root", str(project), "--workflow", "superpowers", "--yes", cwd=project, home=home)
            run_cli("setup", "--type", "project", "--project-root", str(project), "--workflow", "ouroboros", "--force", "--yes", cwd=project, home=home)

            body = (project / "AGENTS.md").read_text()

            self.assertIn("Keep me.", body)
            self.assertEqual(1, body.count("<!-- company-agent-harness:start -->"))
            self.assertIn("Configured workflow engine: `ouroboros`.", body)

    def test_setup_skill_global_installs_managed_skills_for_selected_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            home.mkdir()
            project.mkdir()

            run_cli(
                "setup",
                "--type",
                "skill",
                "--scope",
                "global",
                "--agents",
                "codex,claude",
                "--yes",
                cwd=project,
                home=home,
            )

            codex_skill = home / ".codex" / "skills" / "feature-development-harness"
            claude_skill = home / ".claude" / "skills" / "feature-development-harness"
            marker = codex_skill / ".company-harness-managed.json"

            self.assertTrue((codex_skill / "SKILL.md").is_file())
            self.assertTrue((home / ".codex" / "skills" / "springboot-kotlin-backend-architecture" / "SKILL.md").is_file())
            self.assertTrue((claude_skill / "SKILL.md").is_file())
            self.assertEqual("codex", json.loads(marker.read_text())["agent"])

    def test_uninstall_skill_global_removes_only_managed_skill_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            home.mkdir()
            project.mkdir()

            run_cli("setup", "--type", "skill", "--scope", "global", "--agents", "codex,claude", "--yes", cwd=project, home=home)
            run_cli("uninstall", "--type", "skill", "--scope", "global", "--agents", "codex,claude", "--yes", cwd=project, home=home)

            self.assertFalse((home / ".codex" / "skills" / "feature-development-harness").exists())
            self.assertFalse((home / ".claude" / "skills" / "feature-development-harness").exists())

    def test_setup_both_project_scope_applies_project_harness_and_project_local_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            home.mkdir()
            project.mkdir()

            run_cli(
                "setup",
                "--type",
                "both",
                "--scope",
                "project",
                "--agents",
                "codex,claude",
                "--project-root",
                str(project),
                "--yes",
                cwd=project,
                home=home,
            )

            self.assertTrue((project / ".harness" / "config.yaml").is_file())
            self.assertTrue((project / ".codex" / "skills" / "feature-development-harness" / "SKILL.md").is_file())
            self.assertTrue((project / ".claude" / "skills" / "feature-development-harness" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
