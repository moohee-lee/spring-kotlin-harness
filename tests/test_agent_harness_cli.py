import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "agent-harness.js"


def run_cli(*args: str, cwd: Path, home: Path, check: bool = True, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["HARNESS_SESSION_NOW"] = "2026-05-13T10:11:12+09:00"
    return subprocess.run(
        ["node", str(CLI), *args],
        cwd=cwd,
        env=env,
        text=True,
        input=input_text,
        capture_output=True,
        check=check,
    )


class AgentHarnessCliTest(unittest.TestCase):
    def test_install_command_installs_skills_to_selected_global_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            home.mkdir()
            project.mkdir()

            result = run_cli(
                "install",
                "--location",
                "global",
                "--agents",
                "codex,claude-code,gemini",
                "--yes",
                cwd=project,
                home=home,
            )

            self.assertIn("skill install complete", result.stdout)
            self.assertTrue((home / ".codex" / "skills" / "feature-development-harness" / "SKILL.md").is_file())
            self.assertTrue((home / ".codex" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())
            self.assertTrue((home / ".claude" / "skills" / "feature-development-harness" / "SKILL.md").is_file())
            self.assertTrue((home / ".claude" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())
            self.assertTrue((home / ".gemini" / "skills" / "feature-development-harness" / "SKILL.md").is_file())
            self.assertTrue((home / ".gemini" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())

    def test_install_project_location_uses_explicit_project_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "target-project"
            home.mkdir()
            project.mkdir()

            run_cli(
                "install",
                "--location",
                "project",
                "--project-root",
                str(project),
                "--agents",
                "codex",
                "--yes",
                cwd=root,
                home=home,
            )

            self.assertTrue((project / ".agents" / "skills" / "feature-development-harness" / "SKILL.md").is_file())
            self.assertTrue((project / ".agents" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())

    def test_project_setup_requires_valid_compound_git_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            compound = root / "compound"
            home.mkdir()
            project.mkdir()
            compound.mkdir()

            result = run_cli(
                "project-setup",
                "--compound-root",
                str(compound),
                "--project-root",
                str(project),
                "--workflow",
                "superpowers",
                "--yes",
                cwd=project,
                home=home,
                check=False,
            )

            self.assertNotEqual(0, result.returncode)
            self.assertIn("Compound repository path must be a git clone", result.stderr)

    def test_project_setup_accepts_valid_compound_repo_and_workflow_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            compound = root / "compound"
            home.mkdir()
            project.mkdir()
            compound.mkdir()
            (compound / ".git").mkdir()

            result = run_cli(
                "project-setup",
                "--compound-root",
                str(compound),
                "--project-root",
                str(project),
                "--workflow",
                "oh-my-claudecode",
                "--instructions",
                "claude",
                "--yes",
                cwd=project,
                home=home,
            )

            self.assertIn("project harness setup complete", result.stdout)
            self.assertIn(f"root: {compound}", (project / ".harness" / "config.yaml").read_text())
            self.assertIn("workflow_engine: oh-my-claudecode", (project / ".harness" / "config.yaml").read_text())
            self.assertIn("CLAUDE.md", result.stdout)

    def test_project_setup_with_superpowers_writes_required_subskill_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            compound = root / "compound"
            home.mkdir()
            project.mkdir()
            compound.mkdir()
            (compound / ".git").mkdir()

            run_cli(
                "project-setup",
                "--compound-root",
                str(compound),
                "--project-root",
                str(project),
                "--workflow",
                "superpowers",
                "--yes",
                cwd=project,
                home=home,
            )

            body = (project / "AGENTS.md").read_text()

            self.assertIn("Superpowers Sub-Skill Map", body)
            self.assertIn("MUST use `superpowers:using-superpowers` before any task", body)
            self.assertIn("MUST use `superpowers:test-driven-development` before implementation", body)
            self.assertIn("MUST use `superpowers:systematic-debugging` before fixes", body)
            self.assertIn("MUST use `superpowers:verification-before-completion` before claiming completion", body)
            self.assertIn("If a required Superpowers sub-skill is unavailable", body)
            self.assertIn("MUST run `python3 .harness/scripts/harness_session.py record-turn`", body)
            self.assertIn("python3 .harness/scripts/harness_session.py record-turn", body)
            self.assertIn("Use $compound-engineering-capture", body)
            self.assertIn("Compound Decision", body)
            self.assertTrue((project / ".harness" / "scripts" / "harness_session.py").is_file())

    def test_project_setup_with_non_superpowers_does_not_write_superpowers_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            compound = root / "compound"
            home.mkdir()
            project.mkdir()
            compound.mkdir()
            (compound / ".git").mkdir()

            run_cli(
                "project-setup",
                "--compound-root",
                str(compound),
                "--project-root",
                str(project),
                "--workflow",
                "gstack",
                "--yes",
                cwd=project,
                home=home,
            )

            self.assertNotIn("Superpowers Sub-Skill Map", (project / "AGENTS.md").read_text())

    def test_update_refreshes_managed_skill_installation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            home.mkdir()
            project.mkdir()

            run_cli("install", "--location", "global", "--agents", "codex", "--yes", cwd=project, home=home)
            installed_skill = home / ".codex" / "skills" / "feature-development-harness" / "SKILL.md"
            installed_skill.write_text("stale", encoding="utf-8")

            result = run_cli("update", "--type", "skill", "--location", "global", "--agents", "codex", "--yes", cwd=project, home=home)

            self.assertIn("skill update complete", result.stdout)
            self.assertIn("Feature Development Harness", installed_skill.read_text())

    def test_install_help_explains_location_and_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            project = root / "project"
            home.mkdir()
            project.mkdir()

            result = run_cli("install", "--help", cwd=project, home=home)

            self.assertIn("installation location", result.stdout)
            self.assertIn("global", result.stdout)
            self.assertIn("project", result.stdout)
            self.assertIn("codex", result.stdout)

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
            self.assertTrue((home / ".codex" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())
            self.assertTrue((home / ".codex" / "skills" / "springboot-kotlin-backend-architecture" / "SKILL.md").is_file())
            self.assertTrue((claude_skill / "SKILL.md").is_file())
            self.assertTrue((home / ".claude" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())
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
            self.assertFalse((home / ".codex" / "skills" / "compound-engineering-capture").exists())
            self.assertFalse((home / ".claude" / "skills" / "feature-development-harness").exists())
            self.assertFalse((home / ".claude" / "skills" / "compound-engineering-capture").exists())

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
            self.assertTrue((project / ".agents" / "skills" / "feature-development-harness" / "SKILL.md").is_file())
            self.assertTrue((project / ".agents" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())
            self.assertTrue((project / ".claude" / "skills" / "feature-development-harness" / "SKILL.md").is_file())
            self.assertTrue((project / ".claude" / "skills" / "compound-engineering-capture" / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
