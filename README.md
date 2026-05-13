# Company Feature Development Harness

이 저장소는 여러 프로젝트에서 재사용할 수 있는 에이전트 기능 개발 하네스입니다.

기본 워크플로 엔진은 `superpowers`지만, 프로젝트 설정에서 `gstack`, `ouroboros`, `oh-my-codex` 같은 다른 엔진으로 교체할 수 있게 구성합니다. Spring Boot Kotlin 백엔드 아키텍처 정책은 `skills/springboot-kotlin-backend-architecture`를 우선 적용합니다.

## 구성

```text
skills/
├── feature-development-harness/
├── springboot-kotlin-backend-architecture/
└── springboot-kotlin-initializr/

templates/
├── AGENTS.md
├── harness-config.yaml
└── compound-index.md
```

권장 운영 구조는 세 저장소 분리입니다.

```text
company-agent-harness      # 이 저장소: 스킬, 스크립트, 템플릿
company-agent-compound     # 공유 장기 학습 저장소
target-project/.harness    # 프로젝트별 prompt/답변 요약
```

## Setup 종류

이 하네스에는 서로 다른 두 setup이 있습니다.

```text
skill setup
- Codex, Claude Code, Gemini CLI 같은 에이전트 런타임에 스킬을 설치합니다.
- 예: ~/.codex/skills, ~/.claude/skills, ~/.gemini/extensions

project harness setup
- 실제 기능 개발 대상 프로젝트에 하네스 설정을 적용합니다.
- 예: .harness/config.yaml, .harness/sessions, AGENTS.md managed block
```

기능 개발에 사용하려면 보통 둘 다 필요합니다. 먼저 skill setup으로 에이전트가 `$feature-development-harness`를 인식하게 만들고, 각 서비스 저장소마다 project harness setup을 실행합니다.

## Skill Setup

권장 설치 방식은 `npx`입니다.

```bash
npx @company/agent-harness setup --type skill --scope global --agents codex
npx @company/agent-harness setup --type skill --scope global --agents codex,claude,gemini
```

로컬에서 아직 npm publish 전이라면 저장소 루트에서 같은 CLI를 직접 실행할 수 있습니다.

```bash
node bin/agent-harness.js setup --type skill --scope global --agents codex
```

설치 scope:

```text
global  # 사용자 계정 전체에 스킬 설치
project # 현재 프로젝트 내부에 스킬 설치
both    # global + project 모두 설치
```

agent별 global 설치 위치:

```text
Codex       ${CODEX_HOME:-~/.codex}/skills
Claude Code ~/.claude/skills
Gemini CLI  ~/.gemini/extensions/company-agent-harness
```

agent별 project 설치 위치:

```text
Codex       .codex/skills
Claude Code .claude/skills
Gemini CLI  .gemini/extensions/company-agent-harness
```

shell bootstrapper도 제공합니다.

```bash
curl -fsSL https://raw.githubusercontent.com/company/agent-harness/main/scripts/install.sh | bash -s -- \
  --type skill \
  --scope global \
  --agents codex
```

직접 클론해서 설치할 수도 있습니다.

1. 하네스 저장소를 클론합니다.

   ```bash
   git clone <company-agent-harness-url> company-agent-harness
   cd company-agent-harness
   ```

2. 공유 Compound 저장소를 준비합니다.

   ```bash
   git clone <company-agent-compound-url> ~/work/company-agent-compound
   export HARNESS_COMPOUND_ROOT=~/work/company-agent-compound
   ```

3. Codex가 이 저장소의 스킬을 발견할 수 있게 연결합니다. 사용하는 환경에 맞춰 이 저장소의 `skills/` 디렉터리를 Codex 스킬 경로에 복사하거나 심볼릭 링크로 연결합니다.

   ```bash
   mkdir -p ~/.codex/skills
   ln -s "$(pwd)/skills/feature-development-harness" ~/.codex/skills/feature-development-harness
   ln -s "$(pwd)/skills/springboot-kotlin-backend-architecture" ~/.codex/skills/springboot-kotlin-backend-architecture
   ```

## Project Harness Setup

대상 프로젝트 루트에서 실행합니다.

```bash
npx @company/agent-harness setup \
  --type project \
  --project-root . \
  --compound-root "$HARNESS_COMPOUND_ROOT" \
  --workflow-engine superpowers \
  --instructions agents
```

로컬 저장소에서 실행할 때:

```bash
node /path/to/company-agent-harness/bin/agent-harness.js setup \
  --type project \
  --project-root . \
  --compound-root "$HARNESS_COMPOUND_ROOT" \
  --workflow superpowers \
  --instructions agents
```

skill setup과 project harness setup을 한 번에 하려면:

```bash
npx @company/agent-harness setup \
  --type both \
  --scope project \
  --agents codex,claude \
  --project-root . \
  --workflow superpowers
```

`--instructions`는 프로젝트에 추가할 지시 파일을 선택합니다.

```bash
--instructions agents   # AGENTS.md
--instructions claude   # CLAUDE.md
--instructions gemini   # GEMINI.md
--instructions none     # 지시 파일은 건드리지 않음
```

생성되는 프로젝트 로컬 파일:

```text
.harness/
├── config.yaml
├── .company-harness-managed.json
└── sessions/
```

`setup-project`는 중복 실행해도 managed block을 하나만 유지합니다. 기존 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` 내용은 보존하고 아래 블록만 추가하거나 갱신합니다.

```md
<!-- company-agent-harness:start -->
...
<!-- company-agent-harness:end -->
```

프로젝트 하네스만 제거하려면:

```bash
npx @company/agent-harness uninstall \
  --type project \
  --project-root .
```

기본 uninstall은 `.harness/sessions`를 보존합니다. 세션 요약까지 삭제하려면:

```bash
npx @company/agent-harness uninstall \
  --type project \
  --project-root . \
  --delete-sessions
```

스킬 설치를 제거하려면:

```bash
npx @company/agent-harness uninstall \
  --type skill \
  --scope global \
  --agents codex,claude,gemini
```

스킬과 프로젝트 하네스를 모두 제거하려면:

```bash
npx @company/agent-harness uninstall \
  --type all \
  --scope all \
  --project-root .
```

## 사용 방법

기능 개발을 시작할 때:

```text
Use $feature-development-harness to implement <feature>.
```

작업 시작 요약을 남길 때:

```bash
python3 /path/to/company-agent-harness/skills/feature-development-harness/scripts/harness_session.py \
  start-session \
  --project-root . \
  --topic "Order status API" \
  --prompt-summary "사용자가 주문 상태 변경 API 구현을 요청했다."
```

작업 종료 후 답변 요약을 남길 때:

```bash
python3 /path/to/company-agent-harness/skills/feature-development-harness/scripts/harness_session.py \
  append-answer \
  --session .harness/sessions/2026/05/13/101112-order-status-api.md \
  --answer-summary "헥사고날 계층 경계를 유지하는 구현 방향과 검증 방법을 정리했다." \
  --decision "springboot-kotlin-backend-architecture를 workflow engine보다 우선한다."
```

공유 Compound 노트를 만들 때:

```bash
python3 /path/to/company-agent-harness/skills/feature-development-harness/scripts/harness_session.py \
  compound-note \
  --compound-root "$HARNESS_COMPOUND_ROOT" \
  --category architecture \
  --title "Handler must not call persistence adapter" \
  --tags "springboot-kotlin,hexagonal,adapter-boundary"
```

## 운영 원칙

- `AGENTS.md`는 큰 매뉴얼이 아니라 짧은 지도 역할만 합니다.
- 세부 규칙은 스킬과 `docs`/Compound 기록으로 분리합니다.
- Spring Boot Kotlin 기능 개발에서는 `springboot-kotlin-backend-architecture`가 워크플로 엔진보다 우선합니다.
- prompt/답변 요약은 프로젝트 로컬 `.harness/sessions`에만 둡니다.
- 공유 Compound 저장소에는 반복 방지에 도움이 되는 일반화된 교훈만 남깁니다.

## 검증

```bash
npm test
node bin/agent-harness.js doctor
python3 -m unittest skills/feature-development-harness/tests/test_harness_session.py
python3 /Users/moohee.lee/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/feature-development-harness
```
