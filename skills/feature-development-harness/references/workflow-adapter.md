# Workflow Adapter

The harness owns policy. The workflow engine owns process.

Use this config shape:

```yaml
harness:
  workflow_engine: superpowers
  architecture_skill: springboot-kotlin-backend-architecture
```

Supported engine values are open-ended strings. Treat these as known examples:

- `superpowers`
- `gstack`
- `ouroboros`
- `oh-my-codex`
- `oh-my-claudecode`

When replacing the engine:

1. Keep `.harness/config.yaml` stable.
2. Map the engine's planning, execution, review, and verification hooks to the harness workflow.
3. Do not move architecture policy into the engine.
4. Keep the final Compound capture stage after implementation verification and route it through `compound-engineering-capture`.

If the configured engine is unavailable in the current agent environment, continue with the closest available process skill and call out the fallback in the session summary.

## Superpowers Sub-Skill Map

When `workflow_engine: superpowers`, the harness must map task signals to Superpowers sub-skills explicitly.

This mapping follows the Superpowers upstream workflow: skills are mandatory workflows, and the agent checks for relevant skills before any task. The harness makes the mapping explicit so `workflow_engine: superpowers` is not treated as a loose preference.

| Task signal | Required sub-skill |
| --- | --- |
| Any task starts, including clarification | `superpowers:using-superpowers` |
| New feature, behavior change, design, broad implementation approach | `superpowers:brainstorming` |
| Feature, bugfix, refactor, or behavior change implementation | `superpowers:test-driven-development` |
| Unexpected behavior, failing tests, unclear root cause | `superpowers:systematic-debugging` |
| Approved design or multi-step implementation plan | `superpowers:writing-plans` |
| Executing a written implementation plan | `superpowers:subagent-driven-development` or `superpowers:executing-plans` |
| Substantial work ready for review | `superpowers:requesting-code-review` |
| Applying review feedback | `superpowers:receiving-code-review` |
| Claiming complete, fixed, or tests passing | `superpowers:verification-before-completion` |
| Final integration, PR, merge, cleanup decision | `superpowers:finishing-a-development-branch` |

If a required sub-skill is unavailable in the current runtime, explicitly state the missing sub-skill and continue with the closest fallback. Do not let the fallback override `springboot-kotlin-backend-architecture`.

The installer accepts both names:

```bash
npx github:moohee-lee/spring-kotlin-harness project-setup --workflow superpowers
npx github:moohee-lee/spring-kotlin-harness project-setup --workflow-engine superpowers
```
