---
name: compound-engineering-capture
description: Use when feature work, debugging, review feedback, repeated corrections, shared Compound repositories, or reusable engineering lessons may require a create/update/skip decision.
---

# Compound Engineering Capture

## Overview

This skill applies only the Compound capture and reuse stage. It does not import the full Compound Engineering Plan/Work/Review loop unless the user explicitly asks for it.

The goal is to make the next similar task easier by preserving reusable lessons in the shared Compound repository, while keeping project-local prompt and answer summaries inside the target project.

## Required Flow

1. Read `.harness/config.yaml` and find `harness.compound.root`.
2. Before implementation, search the shared Compound repository for relevant notes:

   ```bash
   rg -n "<domain|error|architecture term>" "$COMPOUND_ROOT"
   ```

3. During work, track mistakes, corrections, unexpected constraints, and review findings that could recur across projects.
4. Before the final response, make exactly one Compound Decision:

   ```text
   Created: <shared note path>
   Updated: <shared note path>
   Skipped: <reason>
   ```

5. Always record the decision in the project-local session turn:

   ```bash
   python3 .harness/scripts/harness_session.py record-turn \
     --project-root . \
     --topic "<short topic>" \
     --prompt-summary "<summary of the user prompt>" \
     --answer-summary "<summary of the assistant work>" \
     --compound-decision "Skipped: no reusable cross-project lesson"
   ```

## Creating Notes

Create or update a shared Compound note only when the lesson is reusable across projects.

Use the project-local script to create the note template:

```bash
python3 .harness/scripts/harness_session.py compound-note \
  --compound-root "$COMPOUND_ROOT" \
  --category "<category>" \
  --title "<reusable lesson title>" \
  --tags "springboot-kotlin,harness,<topic>"
```

Then fill the note with the concrete lesson, not raw transcript text. A useful note has:

- Context: when this lesson applies.
- Wrong Direction: the failure mode or misleading path.
- Correct Pattern: the preferred future behavior.
- Detection: how an agent or reviewer notices the issue early.
- Verification: tests, commands, or checks that prove the corrected pattern.

## Write Policy

Write to the shared Compound repository for:

- Repeated agent mistakes that caused rework.
- Architecture boundary rules that should be remembered across services.
- Test, validation, migration, or API contract patterns that prevent future bugs.
- Review findings that represent a reusable detection rule.

Do not write to the shared Compound repository:

- Raw user prompts or raw assistant answers.
- Secrets, credentials, customer data, internal incident details, or project-only business context.
- One-off implementation details that will not help another project.

If no shared note is created, still record `Skipped: <reason>` in the project-local session.

## Compatibility

If the Every Compound Engineering plugin is installed and a `/ce-compound` equivalent is available, you may use it to help structure the shared note. The harness still requires the project-local `record-turn` entry so every prompt has a local session summary and a Compound Decision.
