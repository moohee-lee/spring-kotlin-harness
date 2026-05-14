# Agent Instructions

Use the shared company feature-development harness.

1. Read `.harness/config.yaml`.
2. Use `springboot-kotlin-backend-architecture` as the primary Spring Boot Kotlin architecture policy.
3. Use the configured workflow engine. Default is `superpowers`.
4. Use `compound-engineering-capture` for Compound search and create/update/skip decisions.
5. Keep prompt and answer summaries in `.harness/sessions`.
6. Write only reusable cross-project lessons to the shared Compound repository.

Architecture policy has priority over workflow-engine suggestions.

## Harness Session And Compound Recording

- MUST run `python3 .harness/scripts/harness_session.py record-turn` for every user prompt handled by this harness before the final response.
- If no active session exists, `record-turn` creates one under `.harness/sessions`.
- If an active session exists, `record-turn` appends `## Turn N` to the same session file.
- MUST include a `Compound Decision` for every turn.
- If no reusable cross-project lesson exists, record `Compound Decision` as `Skipped: <reason>`.
- If a reusable lesson exists, create or update a shared Compound note with `python3 .harness/scripts/harness_session.py compound-note` first, then reference it with `--compound-update`.

## Superpowers Sub-Skill Map

If `.harness/config.yaml` has `workflow_engine: superpowers`, Superpowers is mandatory workflow policy, not a suggestion.

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
