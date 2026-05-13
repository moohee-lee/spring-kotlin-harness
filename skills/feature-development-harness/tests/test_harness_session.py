import subprocess
import sys
import tempfile
import unittest
import os
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "harness_session.py"


def run_cmd(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HARNESS_SESSION_NOW"] = "2026-05-13T10:11:12+09:00"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


class HarnessSessionTest(unittest.TestCase):
    def test_init_project_writes_local_harness_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            compound_root = project_root / "company-compound"

            result = run_cmd(
                "setup-project",
                "--project-root",
                str(project_root),
                "--compound-root",
                str(compound_root),
                "--workflow-engine",
                "superpowers",
                cwd=project_root,
            )

            config = project_root / ".harness" / "config.yaml"
            sessions = project_root / ".harness" / "sessions"
            agents = project_root / "AGENTS.md"
            marker = project_root / ".harness" / ".company-harness-managed.json"

            self.assertIn("created", result.stdout)
            self.assertTrue(config.exists())
            self.assertTrue(sessions.exists())
            self.assertTrue(agents.exists())
            self.assertTrue(marker.exists())
            self.assertIn("workflow_engine: superpowers", config.read_text())
            self.assertIn("architecture_skill: springboot-kotlin-backend-architecture", config.read_text())
            self.assertIn(f"root: {compound_root}", config.read_text())
            self.assertIn("<!-- company-agent-harness:start -->", agents.read_text())
            self.assertIn("Use $feature-development-harness", agents.read_text())

    def test_setup_project_updates_existing_managed_block_without_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            agents = project_root / "AGENTS.md"
            agents.write_text("# Existing Instructions\n\nKeep this line.\n", encoding="utf-8")

            run_cmd(
                "setup-project",
                "--project-root",
                str(project_root),
                "--workflow-engine",
                "superpowers",
                cwd=project_root,
            )
            run_cmd(
                "setup-project",
                "--project-root",
                str(project_root),
                "--workflow-engine",
                "gstack",
                "--force",
                cwd=project_root,
            )

            body = agents.read_text()

            self.assertIn("Keep this line.", body)
            self.assertEqual(1, body.count("<!-- company-agent-harness:start -->"))
            self.assertIn("Configured workflow engine: `gstack`.", body)

    def test_uninstall_project_removes_managed_block_but_preserves_sessions_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_cmd("setup-project", "--project-root", str(project_root), cwd=project_root)
            session_file = project_root / ".harness" / "sessions" / "manual.md"
            session_file.write_text("keep me", encoding="utf-8")

            run_cmd("uninstall-project", "--project-root", str(project_root), cwd=project_root)

            agents_path = project_root / "AGENTS.md"

            self.assertFalse(agents_path.exists())
            self.assertFalse((project_root / ".harness" / "config.yaml").exists())
            self.assertTrue(session_file.exists())

    def test_start_session_creates_project_local_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_cmd("init-project", "--project-root", str(project_root), cwd=project_root)

            result = run_cmd(
                "start-session",
                "--project-root",
                str(project_root),
                "--topic",
                "Order status API",
                "--prompt-summary",
                "사용자가 주문 상태 변경 API 구현을 요청했다.",
                cwd=project_root,
            )

            session_path = Path(result.stdout.strip())
            body = session_path.read_text()

            self.assertTrue(session_path.is_file())
            self.assertEqual("13", session_path.parent.name)
            self.assertIn("# Harness Session: Order status API", body)
            self.assertIn("사용자가 주문 상태 변경 API 구현을 요청했다.", body)
            self.assertIn("## Assistant Answer Summary", body)

    def test_append_answer_summary_updates_existing_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_cmd("init-project", "--project-root", str(project_root), cwd=project_root)
            start = run_cmd(
                "start-session",
                "--project-root",
                str(project_root),
                "--topic",
                "Payment validation",
                "--prompt-summary",
                "결제 검증 규칙을 추가한다.",
                cwd=project_root,
            )
            session_path = Path(start.stdout.strip())

            run_cmd(
                "append-answer",
                "--session",
                str(session_path),
                "--answer-summary",
                "adapter/application/domain 경계를 유지하는 구현 방향을 정리했다.",
                "--decision",
                "architecture skill을 workflow engine보다 우선한다.",
                "--compound-update",
                "solutions/springboot-kotlin/payment-validation-boundary.md",
                cwd=project_root,
            )

            body = session_path.read_text()

            self.assertIn("adapter/application/domain 경계를 유지하는 구현 방향을 정리했다.", body)
            self.assertIn("- architecture skill을 workflow engine보다 우선한다.", body)
            self.assertIn("- solutions/springboot-kotlin/payment-validation-boundary.md", body)

    def test_compound_note_creates_shared_reusable_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            compound_root = project_root / "compound"

            result = run_cmd(
                "compound-note",
                "--compound-root",
                str(compound_root),
                "--category",
                "architecture",
                "--title",
                "Handler must not call persistence adapter",
                "--tags",
                "springboot-kotlin,hexagonal,adapter-boundary",
                cwd=project_root,
            )

            note_path = Path(result.stdout.strip())
            body = note_path.read_text()

            self.assertTrue(note_path.is_file())
            self.assertEqual((compound_root / "solutions" / "architecture").resolve(), note_path.parent.resolve())
            self.assertIn("title: Handler must not call persistence adapter", body)
            self.assertIn("tags: [springboot-kotlin, hexagonal, adapter-boundary]", body)
            self.assertIn("## Correct Pattern", body)


if __name__ == "__main__":
    unittest.main()
