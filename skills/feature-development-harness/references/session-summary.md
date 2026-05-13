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
<short summary, not raw prompt>

## Assistant Answer Summary
<short summary, not raw answer>

## Decisions

## Corrections

## Referenced Compound Notes

## Compound Updates
```

Rules:

- Store summaries, not raw conversation text.
- Keep project-specific context in the project.
- Put cross-project reusable lessons in the shared Compound repository.
- When a session references or creates Compound notes, link them from `Referenced Compound Notes` or `Compound Updates`.
