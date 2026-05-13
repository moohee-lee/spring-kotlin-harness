# Project Layout

Use three storage scopes.

```text
company-agent-harness/
├── package.json
├── bin/
│   └── agent-harness.js
├── skills/
│   ├── feature-development-harness/
│   └── springboot-kotlin-backend-architecture/
├── templates/
├── scripts/
│   └── install.sh
└── README.md
```

```text
company-agent-compound/
├── INDEX.md
├── solutions/
│   ├── architecture/
│   ├── springboot-kotlin/
│   ├── persistence-jooq/
│   └── validation/
├── anti-patterns/
└── decisions/
```

```text
target-project/
├── AGENTS.md
├── .harness/
│   ├── config.yaml
│   ├── .company-harness-managed.json
│   └── sessions/
└── src/
```

Keep `company-agent-compound` outside each project. Point projects to it with `HARNESS_COMPOUND_ROOT` or an absolute path in `.harness/config.yaml`.

Prefer a global clone over a Git submodule for Compound. Compound is long-lived organization memory; submodules make updates too sticky for this use case.

Use the root CLI for setup:

```bash
npx @company/agent-harness setup --type skill --scope global --agents codex
npx @company/agent-harness setup --type project --project-root .
npx @company/agent-harness setup --type both --scope project --agents codex,claude --project-root .
```
