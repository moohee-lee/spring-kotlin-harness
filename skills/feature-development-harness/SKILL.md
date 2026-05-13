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
3. Start a project-local session summary before substantial work:
   ```bash
   python3 <skill-dir>/scripts/harness_session.py start-session \
     --project-root . \
     --topic "<feature or task>" \
     --prompt-summary "<short user prompt summary>"
   ```
4. Search the shared Compound repository configured by `.harness/config.yaml` before implementation. Look for reusable solutions, anti-patterns, and prior corrections.
5. Load and follow `springboot-kotlin-backend-architecture` before touching Spring Boot Kotlin code.
6. Use the configured workflow engine. Default to `superpowers`; switch to `gstack`, `ouroboros`, `oh-my-codex`, or another engine only when the project config says so.
7. Implement and verify using the target project's normal commands.
8. Add a final Compound stage after the execution-review cycle. Capture only reusable mistakes, lessons, and detection rules in the shared Compound repository.
9. Append the assistant answer summary to the project-local session file:
   ```bash
   python3 <skill-dir>/scripts/harness_session.py append-answer \
     --session <session-file> \
     --answer-summary "<short assistant answer summary>"
   ```

## Storage Boundaries

- Project prompt and answer summaries stay in the target project under `.harness/sessions`.
- Shared Compound notes live outside projects in the configured Compound repository.
- Do not write raw prompts, raw answers, secrets, customer data, or project-only business details into shared Compound notes.
- Write to shared Compound only when the lesson can prevent recurrence across projects.

## Resources

- `references/project-layout.md`: repository layout for shared harness, shared Compound, and project-local state.
- `references/workflow-adapter.md`: how to keep `superpowers` replaceable.
- `references/architecture-priority.md`: how to preserve Spring Boot Kotlin architecture policy priority.
- `references/compound-stage.md`: final Compound capture rules.
- `references/session-summary.md`: project-local prompt and answer summary format.
- `scripts/harness_session.py`: Python fallback for project harness setup, session summaries, and shared Compound note templates.
- Repository root `bin/agent-harness.js`: `npx` CLI for `install`, `project-setup`, `update`, uninstall, and doctor checks.
