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

When replacing the engine:

1. Keep `.harness/config.yaml` stable.
2. Map the engine's planning, execution, review, and verification hooks to the harness workflow.
3. Do not move architecture policy into the engine.
4. Keep the final Compound stage after implementation verification.

If the configured engine is unavailable in the current agent environment, continue with the closest available process skill and call out the fallback in the session summary.

The installer accepts both names:

```bash
npx @company/agent-harness setup --type project --workflow superpowers
npx @company/agent-harness setup --type project --workflow-engine superpowers
```
