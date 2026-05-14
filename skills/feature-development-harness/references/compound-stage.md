# Compound Stage

Add this as the final stage after implementation, verification, and review feedback resolution.

Do not import the whole Compound Engineering Plan/Work/Review workflow unless the user asks for it. This harness uses only the capture-and-reuse part.

Use `compound-engineering-capture` as the dedicated skill for this stage.

## Capture Criteria

Write a shared Compound note when at least one is true:

- The agent went in a wrong architectural direction and had to be corrected.
- Review found a repeatable mistake.
- Verification revealed a missing guardrail.
- A reusable detection rule, command, or pattern would prevent recurrence.

Do not write a shared note for:

- One-off project business details.
- Raw prompts or raw answers.
- Secrets, customer data, or private operational context.
- A correction already covered by an existing note.

Even when no shared note is written, record the Compound decision in the project-local session:

```bash
python3 .harness/scripts/harness_session.py record-turn \
  --project-root . \
  --topic "<task>" \
  --prompt-summary "<summary>" \
  --answer-summary "<summary>" \
  --compound-decision "Skipped: no reusable cross-project lesson"
```

## Shared Note Template

```md
---
title: <short reusable lesson>
tags: [springboot-kotlin, architecture]
scope: cross-project
status: draft
---

# <short reusable lesson>

## Context

## Wrong Direction

## Correct Pattern

## Reusable Insight

## Detection

## Verification
```

Use:

```bash
python3 .harness/scripts/harness_session.py compound-note \
  --compound-root "$HARNESS_COMPOUND_ROOT" \
  --category architecture \
  --title "Handler must not call persistence adapter" \
  --tags "springboot-kotlin,hexagonal,adapter-boundary"
```

Then reference the created note from the turn:

```bash
python3 .harness/scripts/harness_session.py record-turn \
  --project-root . \
  --topic "<task>" \
  --prompt-summary "<summary>" \
  --answer-summary "<summary>" \
  --compound-decision "Created reusable lesson" \
  --compound-update "solutions/architecture/handler-must-not-call-persistence-adapter.md"
```
