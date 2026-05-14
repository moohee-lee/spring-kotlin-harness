#!/usr/bin/env python3
"""Project-local harness session summaries and shared Compound notes."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path


DEFAULT_ARCHITECTURE_SKILL = "springboot-kotlin-backend-architecture"
DEFAULT_WORKFLOW_ENGINE = "superpowers"
DEFAULT_SESSION_ROOT = ".harness/sessions"
DEFAULT_COMPOUND_ROOT = "${HARNESS_COMPOUND_ROOT}"
MANAGED_BLOCK_START = "<!-- company-agent-harness:start -->"
MANAGED_BLOCK_END = "<!-- company-agent-harness:end -->"
MANAGED_MARKER = ".harness/.company-harness-managed.json"
ACTIVE_SESSION_MARKER = ".harness/current-session"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "session"


def now() -> datetime:
    fixed = os.environ.get("HARNESS_SESSION_NOW")
    if fixed:
        return datetime.fromisoformat(fixed.replace("Z", "+00:00"))
    return datetime.now().astimezone()


def read_session_root(project_root: Path) -> Path:
    config = project_root / ".harness" / "config.yaml"
    if not config.exists():
        return project_root / DEFAULT_SESSION_ROOT

    in_session_section = False
    for raw_line in config.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == "session_summary:":
            in_session_section = True
            continue
        if in_session_section and line and not raw_line.startswith("    ") and not raw_line.startswith("  "):
            in_session_section = False
        if in_session_section and stripped.startswith("root:"):
            root = stripped.split(":", 1)[1].strip()
            return project_root / root

    return project_root / DEFAULT_SESSION_ROOT


def write_if_allowed(path: Path, content: str, force: bool) -> str:
    if path.exists() and not force:
        return f"exists {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"created {path}"


def project_instruction_block(workflow_engine: str, architecture_skill: str) -> str:
    superpowers_section = ""
    if workflow_engine == "superpowers":
        superpowers_section = """
## Superpowers Sub-Skill Map

Because `.harness/config.yaml` sets `workflow_engine: superpowers`, Superpowers is mandatory workflow policy, not a suggestion.

- MUST use `superpowers:using-superpowers` before any task, including clarifying questions.
- MUST use `superpowers:brainstorming` before designing a new feature, behavior change, or broad implementation approach.
- MUST use `superpowers:test-driven-development` before implementation for any feature, bugfix, refactor, or behavior change.
- MUST use `superpowers:systematic-debugging` before fixes when behavior is unexpected, tests fail, or the root cause is unclear.
- MUST use `superpowers:writing-plans` after an approved design or when executing a multi-step implementation plan.
- MUST use `superpowers:subagent-driven-development` or `superpowers:executing-plans` when executing a written implementation plan.
- MUST use `superpowers:requesting-code-review` before considering substantial implementation work ready.
- MUST use `superpowers:receiving-code-review` before applying review feedback.
- MUST use `superpowers:verification-before-completion` before claiming completion, fixed status, or passing tests.
- MUST use `superpowers:finishing-a-development-branch` when implementation is complete and integration/PR/cleanup decisions are needed.
- If a required Superpowers sub-skill is unavailable in the current agent runtime, explicitly say which sub-skill is unavailable and continue with the closest fallback while preserving the architecture policy.
"""

    return f"""{MANAGED_BLOCK_START}
Use $feature-development-harness for feature development in this project.
Use $compound-engineering-capture for the final Compound capture/reuse decision.

- Read `.harness/config.yaml` before implementation.
- Use `{architecture_skill}` as the primary Spring Boot Kotlin architecture policy.
- Configured workflow engine: `{workflow_engine}`.
- Search the shared Compound repository before implementation.
- Keep prompt and answer summaries in `.harness/sessions`.
- Write only reusable cross-project lessons to the shared Compound repository.

Architecture policy has priority over workflow-engine suggestions.

## Harness Session And Compound Recording

- MUST run `python3 .harness/scripts/harness_session.py record-turn` for every user prompt handled by this harness before the final response.
- If no active session exists, `record-turn` creates one under `.harness/sessions`.
- If an active session exists, `record-turn` appends `## Turn N` to the same session file.
- MUST include a `Compound Decision` for every turn.
- If no reusable cross-project lesson exists, record `Compound Decision` as `Skipped: <reason>`.
- If a reusable lesson exists, create or update a shared Compound note with `python3 .harness/scripts/harness_session.py compound-note` first, then reference it with `--compound-update`.
{superpowers_section}
{MANAGED_BLOCK_END}
"""


def upsert_managed_block(path: Path, block: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# Agent Instructions\n\n{block}", encoding="utf-8")
        return f"created {path}"

    body = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(MANAGED_BLOCK_START)}.*?{re.escape(MANAGED_BLOCK_END)}\n?",
        re.DOTALL,
    )
    if pattern.search(body):
        path.write_text(pattern.sub(block, body), encoding="utf-8")
        return f"updated {path}"

    separator = "\n\n" if body.strip() else ""
    path.write_text(f"{body.rstrip()}{separator}{block}", encoding="utf-8")
    return f"updated {path}"


def remove_managed_block(path: Path) -> str:
    if not path.exists():
        return f"missing {path}"
    body = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"\n*{re.escape(MANAGED_BLOCK_START)}.*?{re.escape(MANAGED_BLOCK_END)}\n*",
        re.DOTALL,
    )
    next_body = pattern.sub("\n", body).strip() + "\n"
    if next_body.strip() == "# Agent Instructions":
        path.unlink()
        return f"removed {path}"
    path.write_text(next_body, encoding="utf-8")
    return f"updated {path}"


def config_yaml(workflow_engine: str, architecture_skill: str, compound_root: str) -> str:
    return f"""harness:
  workflow_engine: {workflow_engine}
  architecture_skill: {architecture_skill}

  compound:
    root: {compound_root}
    mode: shared
    write_policy: reusable_lessons_only

  session_summary:
    root: {DEFAULT_SESSION_ROOT}
    scope: project_local
    store_raw_prompt: false
    store_raw_answer: false
    store_summary: true
"""


def install_project_harness_script(project_root: Path) -> str:
    source = Path(__file__).resolve()
    target = project_root / ".harness" / "scripts" / "harness_session.py"
    existed = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or source != target.resolve():
        shutil.copy2(source, target)
    target.chmod(0o755)
    return f"{'updated' if existed else 'created'} {target}"


def init_project(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    sessions = project_root / DEFAULT_SESSION_ROOT
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / ".gitkeep").touch()

    outputs = []
    outputs.append(install_project_harness_script(project_root))
    outputs.append(write_if_allowed(
        project_root / ".harness" / "config.yaml",
        config_yaml(args.workflow_engine, args.architecture_skill, args.compound_root),
        args.force,
    ))

    marker = {
        "manager": "company-agent-harness",
        "scope": "project",
        "workflowEngine": args.workflow_engine,
        "architectureSkill": args.architecture_skill,
        "compoundRoot": args.compound_root,
    }
    marker_path = project_root / MANAGED_MARKER
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(json.dumps(marker, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    outputs.append(f"created {marker_path}")

    if args.instructions != "none":
        instruction_file = {
            "agents": "AGENTS.md",
            "claude": "CLAUDE.md",
            "gemini": "GEMINI.md",
        }[args.instructions]
        outputs.append(upsert_managed_block(
            project_root / instruction_file,
            project_instruction_block(args.workflow_engine, args.architecture_skill),
        ))

    print("\n".join(outputs))
    return 0


def uninstall_project(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    outputs = []
    for filename in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        path = project_root / filename
        if path.exists() and MANAGED_BLOCK_START in path.read_text(encoding="utf-8"):
            outputs.append(remove_managed_block(path))

    for path in (
        project_root / ".harness" / "config.yaml",
        project_root / MANAGED_MARKER,
        project_root / ".harness" / "scripts" / "harness_session.py",
    ):
        if path.exists():
            path.unlink()
            outputs.append(f"removed {path}")

    scripts_dir = project_root / ".harness" / "scripts"
    if scripts_dir.exists() and not any(scripts_dir.iterdir()):
        scripts_dir.rmdir()
        outputs.append(f"removed {scripts_dir}")

    if args.delete_sessions:
        sessions = project_root / DEFAULT_SESSION_ROOT
        if sessions.exists():
            shutil.rmtree(sessions)
            outputs.append(f"removed {sessions}")

    harness_dir = project_root / ".harness"
    if harness_dir.exists() and not any(harness_dir.iterdir()):
        harness_dir.rmdir()
        outputs.append(f"removed {harness_dir}")

    print("\n".join(outputs) if outputs else f"no managed project harness found in {project_root}")
    return 0


def session_markdown(topic: str, prompt_summary: str) -> str:
    return f"""# Harness Session: {topic}

## User Prompt Summary
{prompt_summary}

## Assistant Answer Summary

## Decisions

## Corrections

## Referenced Compound Notes

## Compound Updates
"""


def active_marker_path(project_root: Path) -> Path:
    return project_root / ACTIVE_SESSION_MARKER


def write_active_session(project_root: Path, session_path: Path) -> None:
    marker = active_marker_path(project_root)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(os.path.relpath(session_path, project_root), encoding="utf-8")


def read_active_session(project_root: Path) -> Path | None:
    marker = active_marker_path(project_root)
    if not marker.exists():
        return None
    raw_path = marker.read_text(encoding="utf-8").strip()
    if not raw_path:
        return None
    session_path = Path(raw_path)
    if not session_path.is_absolute():
        session_path = project_root / session_path
    if not session_path.exists():
        return None
    return session_path


def create_session(project_root: Path, topic: str, prompt_summary: str) -> Path:
    session_root = read_session_root(project_root)
    timestamp = now()
    session_dir = session_root / f"{timestamp:%Y}" / f"{timestamp:%m}" / f"{timestamp:%d}"
    session_dir.mkdir(parents=True, exist_ok=True)

    session_path = session_dir / f"{timestamp:%H%M%S}-{slugify(topic)}.md"
    session_path.write_text(session_markdown(topic, prompt_summary), encoding="utf-8")
    write_active_session(project_root, session_path)
    return session_path


def start_session(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    session_path = create_session(project_root, args.topic, args.prompt_summary)
    print(session_path)
    return 0


def append_list(title: str, items: list[str]) -> str:
    if not items:
        return ""
    lines = "\n".join(f"- {item}" for item in items)
    return f"\n## {title}\n{lines}\n"


def append_answer(args: argparse.Namespace) -> int:
    session = args.session.resolve()
    addition = f"\n## Assistant Answer Summary\n{args.answer_summary}\n"
    addition += append_list("Decisions", args.decision)
    addition += append_list("Corrections", args.correction)
    addition += append_list("Compound Updates", args.compound_update)
    with session.open("a", encoding="utf-8") as output:
        output.write(addition)
    print(session)
    return 0


def bullet_list(items: list[str]) -> str:
    if not items:
        return "- None\n"
    return "\n".join(f"- {item}" for item in items) + "\n"


def next_turn_number(session_path: Path) -> int:
    body = session_path.read_text(encoding="utf-8")
    return len(re.findall(r"^## Turn \d+", body, flags=re.MULTILINE)) + 1


def record_turn(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    session_path = read_active_session(project_root)
    if session_path is None:
        session_path = create_session(project_root, args.topic, args.prompt_summary)

    turn_number = next_turn_number(session_path)
    turn = f"""
## Turn {turn_number}

### User Prompt Summary
{args.prompt_summary}

### Assistant Answer Summary
{args.answer_summary}

### Decisions
{bullet_list(args.decision)}
### Corrections
{bullet_list(args.correction)}
### Referenced Compound Notes
{bullet_list(args.referenced_compound)}
### Compound Decision
{args.compound_decision}

### Compound Updates
{bullet_list(args.compound_update)}
"""
    with session_path.open("a", encoding="utf-8") as output:
        output.write(turn)

    write_active_session(project_root, session_path)
    print(session_path)
    return 0


def compound_markdown(title: str, tags: list[str]) -> str:
    formatted_tags = ", ".join(tags)
    return f"""---
title: {title}
tags: [{formatted_tags}]
scope: cross-project
status: draft
---

# {title}

## Context

## Wrong Direction

## Correct Pattern

## Reusable Insight

## Detection

## Verification
"""


def compound_note(args: argparse.Namespace) -> int:
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    note_dir = args.compound_root.resolve() / "solutions" / slugify(args.category)
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f"{slugify(args.title)}.md"
    note_path.write_text(compound_markdown(args.title, tags), encoding="utf-8")
    print(note_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    def add_project_setup_args(command: argparse.ArgumentParser) -> None:
        command.add_argument("--project-root", type=Path, default=Path("."))
        command.add_argument("--workflow-engine", default=DEFAULT_WORKFLOW_ENGINE)
        command.add_argument("--architecture-skill", default=DEFAULT_ARCHITECTURE_SKILL)
        command.add_argument("--compound-root", default=DEFAULT_COMPOUND_ROOT)
        command.add_argument("--instructions", choices=["agents", "claude", "gemini", "none"], default="agents")
        command.add_argument("--force", action="store_true")

    setup = subcommands.add_parser("setup-project", help="apply harness files to a target project")
    add_project_setup_args(setup)
    setup.set_defaults(func=init_project)

    init = subcommands.add_parser("init-project", help="deprecated alias for setup-project")
    add_project_setup_args(init)
    init.set_defaults(func=init_project)

    uninstall = subcommands.add_parser("uninstall-project", help="remove project-local harness managed files")
    uninstall.add_argument("--project-root", type=Path, default=Path("."))
    uninstall.add_argument("--delete-sessions", action="store_true")
    uninstall.set_defaults(func=uninstall_project)

    start = subcommands.add_parser("start-session", help="create a project-local session summary")
    start.add_argument("--project-root", type=Path, default=Path("."))
    start.add_argument("--topic", required=True)
    start.add_argument("--prompt-summary", required=True)
    start.set_defaults(func=start_session)

    turn = subcommands.add_parser("record-turn", help="append one prompt/answer summary and Compound decision to the active session")
    turn.add_argument("--project-root", type=Path, default=Path("."))
    turn.add_argument("--topic", required=True)
    turn.add_argument("--prompt-summary", required=True)
    turn.add_argument("--answer-summary", required=True)
    turn.add_argument("--compound-decision", required=True)
    turn.add_argument("--decision", action="append", default=[])
    turn.add_argument("--correction", action="append", default=[])
    turn.add_argument("--referenced-compound", action="append", default=[])
    turn.add_argument("--compound-update", action="append", default=[])
    turn.set_defaults(func=record_turn)

    answer = subcommands.add_parser("append-answer", help="append assistant summary to a session")
    answer.add_argument("--session", type=Path, required=True)
    answer.add_argument("--answer-summary", required=True)
    answer.add_argument("--decision", action="append", default=[])
    answer.add_argument("--correction", action="append", default=[])
    answer.add_argument("--compound-update", action="append", default=[])
    answer.set_defaults(func=append_answer)

    compound = subcommands.add_parser("compound-note", help="create a shared reusable lesson note")
    compound.add_argument("--compound-root", type=Path, required=True)
    compound.add_argument("--category", required=True)
    compound.add_argument("--title", required=True)
    compound.add_argument("--tags", default="")
    compound.set_defaults(func=compound_note)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
