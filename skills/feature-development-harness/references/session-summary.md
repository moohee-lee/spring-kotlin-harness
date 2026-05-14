# Session Summary

Prompt and answer summaries are project-local state.

Default location:

```text
.harness/sessions/YYYY/MM/DD/HHMMSS-<topic>.md
```

Default shape:

```md
# Harness Session: <topic>

## User Prompt Summary
<initial short summary, not raw prompt>

## Assistant Answer Summary

## Decisions

## Corrections

## Referenced Compound Notes

## Compound Updates

## Turn 1

### User Prompt Summary
<short summary, not raw prompt>

### Assistant Answer Summary
<short summary, not raw answer>

### Decisions

### Corrections

### Referenced Compound Notes

### Compound Decision
Skipped: <reason>, or Created/Updated: <shared note path>

### Compound Updates
```

Rules:

- Store summaries, not raw conversation text.
- Use `python3 .harness/scripts/harness_session.py record-turn` for every user prompt handled by the harness.
- Keep one active session per task and append `## Turn N` for follow-up prompts.
- Keep project-specific context in the project.
- Put cross-project reusable lessons in the shared Compound repository.
- Every turn must include a `Compound Decision`.
- If a session references or creates Compound notes, link them from `Referenced Compound Notes` or `Compound Updates`.
