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
            script = project_root / ".harness" / "scripts" / "harness_session.py"

            self.assertIn("created", result.stdout)
            self.assertTrue(config.exists())
            self.assertTrue(sessions.exists())
            self.assertTrue(agents.exists())
            self.assertTrue(marker.exists())
            self.assertTrue(script.exists())
            self.assertIn("workflow_engine: superpowers", config.read_text())
            self.assertIn("architecture_skill: springboot-kotlin-backend-architecture", config.read_text())
            self.assertIn(f"root: {compound_root}", config.read_text())
            self.assertIn("<!-- company-agent-harness:start -->", agents.read_text())
            self.assertIn("Use $feature-development-harness", agents.read_text())
            self.assertIn("Use $compound-engineering-capture", agents.read_text())
            self.assertIn("python3 .harness/scripts/harness_session.py record-turn", agents.read_text())
            self.assertIn("Superpowers Sub-Skill Map", agents.read_text())
            self.assertIn("superpowers:test-driven-development", agents.read_text())
            self.assertIn("superpowers:verification-before-completion", agents.read_text())

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
            active = project_root / ".harness" / "current-session"
            self.assertTrue(active.exists())
            self.assertEqual(session_path.resolve(), (project_root / active.read_text().strip()).resolve())

    def test_record_turn_creates_active_session_and_logs_compound_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_cmd("init-project", "--project-root", str(project_root), cwd=project_root)

            result = run_cmd(
                "record-turn",
                "--project-root",
                str(project_root),
                "--topic",
                "IP owner ref contract",
                "--prompt-summary",
                "operation 필드를 제거하고 null organizationId/networkId를 delete로 처리 요청.",
                "--answer-summary",
                "request contract와 tombstone 처리 기준을 테스트와 구현에 반영.",
                "--compound-decision",
                "Skipped: reusable cross-project lesson 없음.",
                cwd=project_root,
            )

            session_path = Path(result.stdout.strip())
            body = session_path.read_text()

            self.assertTrue(session_path.is_file())
            self.assertIn("## Turn 1", body)
            self.assertIn("operation 필드를 제거", body)
            self.assertIn("request contract와 tombstone 처리", body)
            self.assertIn("### Compound Decision", body)
            self.assertIn("Skipped: reusable cross-project lesson 없음.", body)

    def test_record_turn_appends_to_existing_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            run_cmd("init-project", "--project-root", str(project_root), cwd=project_root)
            first = run_cmd(
                "record-turn",
                "--project-root",
                str(project_root),
                "--topic",
                "UUID normalization",
                "--prompt-summary",
                "하이픈 없는 UUID도 허용 요청.",
                "--answer-summary",
                "UUID 정규화 테스트를 추가.",
                "--compound-decision",
                "Skipped: 기존 validation 패턴 안에서 해결.",
                cwd=project_root,
            )
            first_path = Path(first.stdout.strip())

            second = run_cmd(
                "record-turn",
                "--project-root",
                str(project_root),
                "--topic",
                "Ignored when active session exists",
                "--prompt-summary",
                "추가 검증 요청.",
                "--answer-summary",
                "관련 테스트를 실행.",
                "--compound-decision",
                "Created reusable lesson.",
                "--compound-update",
                "solutions/validation/uuid-normalization.md",
                cwd=project_root,
            )

            second_path = Path(second.stdout.strip())
            body = first_path.read_text()

            self.assertEqual(first_path.resolve(), second_path.resolve())
            self.assertIn("## Turn 1", body)
            self.assertIn("## Turn 2", body)
            self.assertIn("solutions/validation/uuid-normalization.md", body)

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
