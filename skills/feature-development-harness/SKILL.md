---
name: feature-development-harness
description: Use when developing features across company projects with a reusable agent harness, pluggable workflow engine, Spring Boot Kotlin architecture rules, shared Compound learning, or project-local prompt and answer summaries.
---

# Feature Development Harness

## Overview

Use this skill as the feature-development entry point for company projects. It keeps the workflow engine replaceable while making `springboot-kotlin-backend-architecture` the primary architecture policy for Spring Boot Kotlin backend work.

## Priority Order

Apply rules in this order:

1. User and company instructions.
2. `springboot-kotlin-backend-architecture`.
3. The target project's `AGENTS.md`, README, build, and test conventions.
4. The configured workflow engine, such as `superpowers`, `gstack`, `ouroboros`, or `oh-my-codex`.
5. General model judgment.

If the workflow engine suggests a structure that conflicts with the architecture skill, treat the architecture skill as authoritative.

## Workflow

1. Confirm that skill setup and project harness setup are both handled. `install` makes the agent runtime discover this skill. `project-setup` applies `.harness/config.yaml`, `.harness/sessions`, and a managed instruction block to the target repository. Prefer the `npx github:moohee-lee/spring-kotlin-harness` CLI when available.
2. Read `.harness/config.yaml` in the target project. If missing, initialize it with:
   ```bash
   npx github:moohee-lee/spring-kotlin-harness project-setup --project-root .
   ```
3. For every user prompt handled by this harness, record a project-local turn summary before the final response. `record-turn` creates a session if none is active and appends to the active session otherwise:
   ```bash
   python3 .harness/scripts/harness_session.py record-turn \
     --project-root . \
     --topic "<feature or task>" \
     --prompt-summary "<short user prompt summary>" \
     --answer-summary "<short assistant answer summary>" \
     --compound-decision "Skipped: no reusable cross-project lesson"
   ```
4. Use `compound-engineering-capture` for shared Compound search, create/update/skip decisions, and reusable lesson capture. Search the shared Compound repository configured by `.harness/config.yaml` before implementation.
5. Load and follow `springboot-kotlin-backend-architecture` before touching Spring Boot Kotlin code.
6. Use the configured workflow engine. Default to `superpowers`; switch to `gstack`, `ouroboros`, `oh-my-codex`, or another engine only when the project config says so.
7. Implement and verify using the target project's normal commands.
8. Add a final Compound stage after the execution-review cycle. Capture only reusable mistakes, lessons, and detection rules in the shared Compound repository. If there is no reusable lesson, record the skip reason in `--compound-decision`.

## Superpowers Mapping

When `.harness/config.yaml` has `workflow_engine: superpowers`, treat Superpowers as mandatory workflow policy:

- Use `superpowers:using-superpowers` before any task.
- Use `superpowers:brainstorming` before designing a new feature, behavior change, or broad implementation approach.
- Use `superpowers:test-driven-development` before implementation for any feature, bugfix, refactor, or behavior change.
- Use `superpowers:systematic-debugging` before fixes when behavior is unexpected, tests fail, or the root cause is unclear.
- Use `superpowers:writing-plans` after an approved design or for multi-step implementation plans.
- Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` when executing a written implementation plan.
- Use `superpowers:requesting-code-review` before considering substantial implementation work ready.
- Use `superpowers:receiving-code-review` before applying review feedback.
- Use `superpowers:verification-before-completion` before claiming completion, fixed status, or passing tests.
- Use `superpowers:finishing-a-development-branch` when implementation is complete and integration/PR/cleanup decisions are needed.
- If a required Superpowers sub-skill is unavailable, say which one is unavailable and continue with the closest fallback while preserving the architecture policy.

## Storage Boundaries

- Project prompt and answer summaries stay in the target project under `.harness/sessions`.
- Shared Compound notes live outside projects in the configured Compound repository.
- Do not write raw prompts, raw answers, secrets, customer data, or project-only business details into shared Compound notes.
- Write to shared Compound only when the lesson can prevent recurrence across projects.

## Resources

- `references/project-layout.md`: repository layout for shared harness, shared Compound, and project-local state.
- `references/workflow-adapter.md`: how to keep `superpowers` replaceable and map its sub-skills.
- `references/architecture-priority.md`: how to preserve Spring Boot Kotlin architecture policy priority.
- `compound-engineering-capture`: separate capture-only skill for shared Compound decisions and note policy.
- `references/compound-stage.md`: final Compound capture rules.
- `references/session-summary.md`: project-local prompt and answer summary format.
- `scripts/harness_session.py`: Python fallback for project harness setup, per-turn session summaries, and shared Compound note templates.
- Repository root `bin/agent-harness.js`: `npx` CLI for `install`, `project-setup`, `update`, uninstall, and doctor checks.
