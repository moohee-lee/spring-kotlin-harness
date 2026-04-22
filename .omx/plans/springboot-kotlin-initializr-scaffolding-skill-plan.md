# Spring Boot Kotlin Initializr Scaffolding Skill Plan

## 요구사항 요약

Spring Boot Kotlin 프로젝트를 Spring Initializr로 생성한 뒤, `moohee-lee/springboot-kotlin-skeleton`의 공통 아키텍처/설정 파일을 적용해 빌드 가능한 백엔드 프로젝트로 스캐폴딩하는 Codex skill을 만든다.

고정 Initializr 값:

- Project/type: `gradle-project-kotlin`
- Language: `kotlin`
- Packaging: `jar`
- Configuration file format: `yaml`

사용자 입력 값:

- Spring Boot 버전
- Java 버전
- Kotlin 버전 선택 방식
- Group
- Artifact

고정 파생 값:

- Package name: `{group}.{artifact}`
- `artifact=default`이면 현재 폴더명 사용
- `boot`, `java`, `kotlin`, `artifact`가 없거나 `default`이면 Initializr 기본값 사용

사용자 입력 형식:

```text
boot=<boot-version>, java=<java-version>, kotlin=default, artifact=default, group=com.example
```

전체 사용자 흐름:

1. Spring Initializr metadata를 조회해 추천값을 보여준다.
2. 사용자가 생성 파라미터를 입력한다.
3. 선택한 Boot 버전에 맞는 의존성 목록을 조회한다.
4. `SPRING_INITIALIZR_DEPENDENCIES.md` 체크박스 파일을 생성하고 사용자에게 수정 요청한다.
5. 사용자가 수정 완료를 알리면 체크된 dependency id를 파싱한다.
6. Spring Initializr `starter.zip`으로 프로젝트를 생성한다.
7. `SPRING_INITIALIZR_DEPENDENCIES.md`를 삭제한다.
8. `springboot-kotlin-skeleton`을 분석/적용한다.
9. 예시용 sample domain 파일은 제외하고, common/config/resources/buildSrc/기본 패키지 구조를 새 프로젝트에 적용한다.
10. 생성 프로젝트를 빌드해 정상 빌드 여부를 확인한다.

## 근거

- Spring Initializr 공식 문서는 Initializr가 JVM 프로젝트 생성과 사용 가능한 dependency/version metadata 조회 API를 제공한다고 설명한다.
- 공식 문서의 project generation model은 `groupId`, `artifactId`, build system, packaging, configuration file format, language, dependencies, platform version, root package name을 포함한다.
- 공식 문서는 `/starter.zip`이 전체 프로젝트 zip을 생성하고, generation 요청에서 `dependencies`, `bootVersion` 같은 파라미터를 사용한다고 설명한다.
- 공식 metadata endpoint 확인 결과, 현재 `starter.zip` link는 `type`, `dependencies`, `packaging`, `javaVersion`, `language`, `bootVersion`, `groupId`, `artifactId`, `name`, `description`, `packageName`, `configurationFileFormat` 파라미터를 지원한다.
- 현재 metadata에는 `gradle-project-kotlin`, `kotlin`, `jar`, `yaml` 선택지가 존재한다.
- 현재 `/dependencies?bootVersion=...` 응답은 dependency id별 resolved coordinate, scope, BOM, repository 정보를 제공한다.
- `springboot-kotlin-skeleton`에는 `buildSrc`, `config/detekt`, `common`, WebFlux/error/i18n/WebClient/jOOQ/transaction 설정, resources, tests, sample domain 파일이 포함되어 있다.

## 제안 스킬 형태

추천 skill name: `springboot-kotlin-initializr`

대체 후보:

- `springboot-kotlin-scaffold`
- `springboot-kotlin-bootstrap`
- `springboot-kotlin-initializr-scaffold`

추천 생성 위치: 사용자가 별도 지정하지 않으면 `${CODEX_HOME:-$HOME/.codex}/skills`; 이 워크스페이스에서 계속 관리하려면 `./skills`.

구성:

```text
springboot-kotlin-initializr/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── initializr-flow.md
│   ├── dependency-selection.md
│   ├── skeleton-overlay.md
│   ├── buildsrc-version-policy.md
│   └── verification.md
└── scripts/
    ├── initializr_metadata.py
    ├── write_dependency_checklist.py
    ├── parse_dependency_checklist.py
    ├── create_initializr_project.py
    └── apply_skeleton_overlay.py
```

`scripts/`를 포함하는 이유:

- Initializr metadata JSON 파싱, compatibility filtering, dependency checklist 생성/파싱, zip 다운로드/압축해제, package path 변환은 반복적이고 실수 여지가 크다.
- Skill 본문에 curl/jq/manual zip 처리 절차를 길게 넣는 것보다 스크립트로 낮은 자유도를 주는 편이 안전하다.

## 구현 계획

### 1. `SKILL.md` 작성

`SKILL.md`는 500줄 미만으로 유지한다.

포함 내용:

- 이 스킬의 목적: Spring Initializr 기반 Spring Boot Kotlin 프로젝트 생성 + skeleton overlay.
- 고정 Initializr 값:
  - `type=gradle-project-kotlin`
  - `language=kotlin`
  - `packaging=jar`
  - `configurationFileFormat=yaml`
- 사용자 입력 포맷:
  - `boot=..., java=..., kotlin=default, artifact=default, group=...`
- 기본값 규칙:
  - 항목 누락 또는 `default`는 Initializr 기본값 사용.
  - `artifact=default`는 현재 폴더명 사용.
  - `packageName={group}.{artifact}`.
- 두 단계 상호작용:
  - 1차: metadata 추천값 제공 후 생성 파라미터 입력 요청.
  - 2차: dependency checklist 생성 후 사용자가 체크박스를 수정하면 이어서 생성.
- 생성 후 `SPRING_INITIALIZR_DEPENDENCIES.md` 삭제 규칙.
- references/scripts 사용 순서.
- 실패/중단 복구 규칙.

### 2. `references/initializr-flow.md`

Initializr API 흐름을 문서화한다.

포함 내용:

- Metadata 조회:
  ```bash
  GET https://start.spring.io/metadata/client
  Accept: application/vnd.initializr.v2.3+json
  User-Agent: <client-id>/<version>
  ```
- Dependency resolution 조회:
  ```bash
  GET https://start.spring.io/dependencies?bootVersion=<boot>
  ```
- Project 생성:
  ```bash
  GET https://start.spring.io/starter.zip
  ```
- 생성 파라미터:
  - `type=gradle-project-kotlin`
  - `language=kotlin`
  - `packaging=jar`
  - `configurationFileFormat=yaml`
  - `bootVersion=<boot>` only when not default
  - `javaVersion=<java>` only when not default
  - `groupId=<group>`
  - `artifactId=<artifact>`
  - `name=<artifact>`
  - `packageName=<group>.<artifact>`
  - `dependencies=<comma-separated dependency ids>`
- Kotlin version 추천값:
  - Initializr metadata가 Kotlin version을 직접 제공하지 않을 수 있으므로, 선택한 Boot/Java로 작은 probe project 또는 build.gradle endpoint를 생성해 `kotlin("jvm") version` 값을 읽는 방식을 문서화한다.
  - `kotlin=default`이면 Initializr 생성값을 유지한다.
  - 사용자가 Kotlin 버전을 명시하면 생성 후 `buildSrc/PluginVersions.kt`와 `build.gradle.kts`에 반영한다.
- Initializr가 사용자가 요청한 Java version을 실제 build file에 다르게 반영할 수 있으므로, 생성 후 `build.gradle.kts`의 `JavaLanguageVersion.of(...)`를 검증하고 mismatch를 보고한다.

### 3. `references/dependency-selection.md`

`SPRING_INITIALIZR_DEPENDENCIES.md` 생성/파싱 규칙을 문서화한다.

Markdown 형식:

```markdown
# Spring Initializr Dependencies

Generated for:
- boot: 4.0.5
- java: default
- group: com.example
- artifact: demo
- package: com.example.demo

Instructions:
- `[ ]`를 `[x]`로 바꿔 설치할 의존성을 선택하세요.
- dependency id는 수정하지 마세요.

## Web
- [ ] `webflux` - Spring Reactive Web: Build reactive web applications with Spring WebFlux and Netty.
- [ ] `spring-webclient` - Reactive HTTP Client: Spring Boot integration for WebClient.
```

규칙:

- Initializr category 순서를 보존한다.
- 각 항목은 dependency id, name, description, versionRange를 보여준다.
- 선택한 Boot 버전과 호환되지 않는 dependency는 기본적으로 제외한다.
- 호환 여부가 애매한 dependency는 "주의" 표시를 달고 선택 가능하게 둘지, 아예 제외할지 스킬 구현 시 정책을 정한다. 기본 권장: `/dependencies?bootVersion` resolved map에 없는 항목은 제외.
- Markdown parser는 `- [x] \`dependency-id\`` 또는 `- [X] \`dependency-id\``만 선택으로 인정한다.
- 사용자가 파일을 수정하지 않은 상태로 계속하면 dependency 없이 생성할 수 있지만, 한 번 확인 메시지를 남긴다.

### 4. `references/skeleton-overlay.md`

`springboot-kotlin-skeleton` 적용 규칙을 문서화한다.

적용 대상:

- `buildSrc/`
- `config/detekt/`
- `src/main/kotlin/{basePackage}/common/**`
- `src/main/kotlin/{basePackage}/adapter/output/persistence/config/DatabasePersistenceConfiguration.kt`
- `src/main/kotlin/{basePackage}/adapter/output/transaction/TransactionalExecutorAdapter.kt`
- `src/main/kotlin/{basePackage}/application/port/output/transaction/TransactionalPort.kt`
- `src/main/resources/errors/`
- `src/main/resources/enums/`
- `src/main/resources/messages/`
- `src/main/resources/validations/`
- `src/main/resources/db/schema.sql` only if jOOQ or SQL skeleton support is selected/needed.
- `src/test/resources/application-test.yml` when matching datasource/test setup is selected.

제외 대상:

- `domain/sample/**`
- `application/port/input/sample/**`
- `application/port/output/sample/**`
- `application/service/SampleService.kt`
- `adapter/input/web/sample/**`
- `adapter/output/persistence/jooq/sample/**`
- `common/errors/SampleErrorCode.kt`
- `common/exception/SampleNotFoundException.kt`
- sample 관련 test files.
- README/HELP/sample API 문서.

패키지 변환:

- Skeleton의 `com.example.skeleton`을 `{group}.{artifact}`로 치환한다.
- 파일 경로도 `src/main/kotlin/com/example/skeleton`에서 target package path로 이동한다.
- Artifact가 hyphen을 포함하면 package segment에는 Kotlin package로 안전한 정규화가 필요하다.
  - 예: `my-service` -> `myservice` 또는 user-defined normalized segment.
  - 사용자 요구는 `{Group}.{Artifact}` 고정이므로, 스킬은 Artifact가 Kotlin package identifier로 유효한지 검사하고 유효하지 않으면 에러로 멈추거나 명확히 변환 정책을 적용해야 한다.
  - 권장: 처음 계획 단계에서 artifact는 package segment로 유효한 값만 허용한다.

Build merge:

- Initializr가 생성한 `settings.gradle.kts`, wrapper, 기본 app class, test class는 유지한다.
- `build.gradle.kts`는 Initializr 결과를 기준으로 skeleton build 설정을 병합한다.
- Skeleton의 버전은 그대로 강제하지 않고, 생성된 Boot/Kotlin/Java 버전을 `buildSrc` 상수로 옮긴다.
- 사용자가 선택한 dependency는 유지하고, skeleton에 필요한 WebFlux/Validation/jOOQ/WebClient/Configuration Processor/Coroutine/Jackson/Micrometer 의존성을 누락 시 추가한다.

### 5. `references/buildsrc-version-policy.md`

버전 관리 정책을 문서화한다.

규칙:

- Initializr가 생성한 plugin version을 `buildSrc/src/main/kotlin/PluginVersions.kt`로 이동한다.
  - `KOTLIN`
  - `SPRING_BOOT`
  - `SPRING_DEPENDENCY_MANAGEMENT`
  - `JOOQ` if plugin exists
  - `DETEKT` if detekt is applied
- Java toolchain version은 `BuildVersions.kt`로 이동한다.
- Spring Boot BOM이 관리하는 dependency에는 버전을 직접 쓰지 않는다.
- 직접 버전이 필요한 dependency만 `DependencyVersions.kt`에 추가한다.
- 외부 dependency를 추가할 때 `build.gradle.kts`에 `"1.2.3"` literal을 쓰지 않는다.
- Initializr resolved dependency가 explicit BOM/repository를 요구하면 해당 BOM/repository를 Gradle에 반영한다.

예시:

```kotlin
object PluginVersions {
    const val KOTLIN = "2.2.21"
    const val SPRING_BOOT = "4.0.5"
    const val SPRING_DEPENDENCY_MANAGEMENT = "1.1.7"
}
```

```kotlin
plugins {
    kotlin("jvm") version PluginVersions.KOTLIN
    kotlin("plugin.spring") version PluginVersions.KOTLIN
    id("org.springframework.boot") version PluginVersions.SPRING_BOOT
    id("io.spring.dependency-management") version PluginVersions.SPRING_DEPENDENCY_MANAGEMENT
}
```

### 6. `references/verification.md`

검증 절차를 문서화한다.

필수 확인:

- `SPRING_INITIALIZR_DEPENDENCIES.md`가 프로젝트 생성 후 삭제된다.
- `application.yaml`이 생성되고 `.properties`가 남지 않는다.
- `packageName`이 `{group}.{artifact}`로 반영되어 있다.
- Main application class package와 경로가 일치한다.
- `buildSrc`가 compile classpath에서 정상 인식된다.
- `build.gradle.kts`에 raw plugin/dependency version literal이 남지 않는다. 단, Spring Boot BOM이 관리하지 않는 dependency version은 `DependencyVersions` 참조여야 한다.
- Sample domain 파일이 남지 않는다.
- `common` package와 resources message bundle이 target package로 적용된다.
- `./gradlew build` 또는 가능한 최소 검증 명령이 성공한다.

검증 명령:

```bash
./gradlew jooqCodegen
./gradlew compileKotlin
./gradlew test
./gradlew build
```

`jooqCodegen`은 jOOQ plugin/schema가 적용된 경우에만 실행한다.

### 7. `scripts/initializr_metadata.py`

역할:

- `metadata/client`를 조회한다.
- 현재 사용 가능한 Boot versions, Java versions, default 값, Kotlin 생성 기본값을 요약한다.
- `artifact=default` 추천값으로 현재 폴더명을 제공한다.
- 선택한 Boot version으로 probe build를 생성해 Kotlin plugin version을 추출한다.
- 사용자에게 보여줄 추천 문구를 출력한다.

출력 예:

```text
추천 생성 값
- Spring Boot: 4.0.5
- Java: 17 (Initializr default)
- Kotlin: Spring Boot 4.0.5 생성 기본값은 2.2.21
- Artifact 기본값: spring-kotlin-initializr-test

입력 형식:
boot=<boot-version>, java=<java-version>, kotlin=default, artifact=default, group=com.example
```

주의:

- Spring Initializr metadata와 실제 generated build 사이에 차이가 있을 수 있으므로 probe 결과를 함께 표시한다.
- "RELEASE" suffix는 현재 Initializr가 실제 id로 제공하는 값과 다를 수 있으므로 metadata id를 우선한다.

### 8. `scripts/write_dependency_checklist.py`

입력:

- `--boot`
- `--java`
- `--kotlin`
- `--group`
- `--artifact`
- `--output SPRING_INITIALIZR_DEPENDENCIES.md`

역할:

- `/metadata/client`와 `/dependencies?bootVersion=<boot>`를 조회한다.
- 호환 dependency를 category별로 정렬한다.
- Markdown checkbox file을 생성한다.
- hidden metadata comment에 생성 파라미터를 보존한다.

예:

```markdown
<!-- spring-initializr: boot=4.0.5 java=default kotlin=default group=com.example artifact=demo package=com.example.demo -->
```

### 9. `scripts/parse_dependency_checklist.py`

역할:

- `SPRING_INITIALIZR_DEPENDENCIES.md`를 읽는다.
- 체크된 dependency ids를 JSON 또는 comma-separated 형태로 출력한다.
- hidden metadata comment에서 boot/java/kotlin/group/artifact/package 값을 복구한다.
- dependency id가 Initializr metadata에 없는 경우 오류로 중단한다.

### 10. `scripts/create_initializr_project.py`

역할:

- 체크된 dependency id와 생성 파라미터로 `starter.zip`을 다운로드한다.
- 대상 디렉터리에 안전하게 압축을 푼다.
- 기존 파일이 있으면 overwrite 정책을 명확히 적용한다.
- 생성 직후 build.gradle.kts, settings.gradle.kts, application.yaml, package path를 sanity check한다.
- 성공하면 `SPRING_INITIALIZR_DEPENDENCIES.md`를 삭제한다.

안전 규칙:

- 비어 있지 않은 디렉터리에 생성할 때는 overwrite 계획을 먼저 보고하고, 스킬은 사용자 승인을 요구해야 한다.
- 기존 사용자 파일을 삭제하지 않는다.
- 실패 시 zip과 임시 디렉터리를 보존하거나 경로를 출력해 디버깅할 수 있게 한다.

### 11. `scripts/apply_skeleton_overlay.py`

역할:

- `springboot-kotlin-skeleton`을 GitHub archive 또는 git clone으로 임시 디렉터리에 가져온다.
- 적용 대상/제외 대상 manifest를 기준으로 파일을 복사한다.
- package declaration과 import를 target package로 바꾼다.
- sample domain 관련 파일은 복사하지 않는다.
- Initializr build 설정을 skeleton buildSrc 방식으로 변환한다.
- 필요한 dependency/plugin/configuration processor 설정을 병합한다.

구현 방식:

- 단순 문자열 치환은 package/import/resource path에만 제한한다.
- Gradle 파일 수정은 가능한 한 구조적/섹션 기반으로 처리한다.
- 변경 전후 파일 목록을 출력한다.
- build merge가 애매하면 자동 변경보다 TODO report를 남기고 중단한다.

## Acceptance Criteria

- Skill folder가 `quick_validate.py`를 통과한다.
- `SKILL.md`는 frontmatter에 `name`, `description`만 포함한다.
- `SKILL.md`는 두 단계 사용자 흐름과 생성/적용/검증 순서를 명확히 안내한다.
- Initializr 고정값이 정확히 반영된다: `gradle-project-kotlin`, `kotlin`, `jar`, `yaml`.
- 사용자 입력 parser는 요청 형식과 `default`/누락 처리 규칙을 지원한다.
- Metadata 조회 스크립트는 Boot/Java/default 추천값과 Kotlin probe 버전을 출력한다.
- Dependency checklist는 `SPRING_INITIALIZR_DEPENDENCIES.md`로 생성되고, 체크된 dependency id를 안정적으로 파싱한다.
- Project generation script는 checked dependency로 `starter.zip`을 생성한다.
- 성공 후 `SPRING_INITIALIZR_DEPENDENCIES.md`를 삭제한다.
- Skeleton overlay는 sample domain 파일을 제외하고 common/config/resources/buildSrc/transaction/persistence 설정을 target package로 적용한다.
- Build merge 후 plugin/dependency version literal은 `buildSrc` 상수로 이동한다.
- Spring Boot BOM이 관리하는 dependency에는 직접 버전을 붙이지 않는다.
- 최종 프로젝트가 `./gradlew build` 또는 해당 프로젝트에서 가능한 검증 명령을 통과한다.

## Risks And Mitigations

- Risk: Spring Initializr metadata와 실제 generated build.gradle.kts가 다를 수 있다.
  - Mitigation: metadata만 믿지 말고 probe project/build로 Kotlin plugin version과 Java toolchain 반영값을 확인한다.

- Risk: Artifact 값이 Kotlin package segment로 유효하지 않을 수 있다.
  - Mitigation: `{group}.{artifact}` 고정 요구를 지키기 위해 artifact identifier validation을 수행한다. 유효하지 않으면 수정 요청 또는 명확한 normalization 정책이 필요하다.

- Risk: 비어 있지 않은 디렉터리에 starter.zip을 풀며 사용자 파일을 덮어쓸 수 있다.
  - Mitigation: overwrite 전 파일 충돌 목록을 출력하고 사용자 승인을 받는다.

- Risk: Skeleton build.gradle.kts와 Initializr build.gradle.kts 병합이 Boot 버전에 따라 깨질 수 있다.
  - Mitigation: Initializr 결과를 source of truth로 삼고, skeleton의 architecture/config dependency만 병합한다. 버전은 생성값을 `buildSrc`로 이동한다.

- Risk: Skeleton sample 파일이 새 프로젝트에 남아 불필요한 API/domain이 생길 수 있다.
  - Mitigation: 명시적 exclude manifest와 post-copy search로 `sample`, `Sample` 잔여물을 검사한다.

- Risk: 선택 dependency에 따라 BOM/repository가 필요한데 누락될 수 있다.
  - Mitigation: `/dependencies?bootVersion`의 `boms`, `repositories` 정보를 반영하거나 Initializr가 생성한 build.gradle.kts를 유지한다.

- Risk: WebFlux/jOOQ skeleton overlay가 사용자가 선택하지 않은 dependency를 요구한다.
  - Mitigation: overlay 전 필수 dependency set을 계산하고 누락 dependency를 자동 추가하거나 report 후 사용자 확인을 받는다.

## Verification Plan

1. Unit-level script checks:
   - Input parser: missing/default/custom values.
   - Dependency markdown writer/parser.
   - Package name validation.
   - Sample exclude manifest.

2. Integration dry run:
   - Metadata 조회.
   - Dependency checklist 생성.
   - Mocked checked dependencies 파싱.
   - `starter.zip` 생성.
   - Skeleton overlay 적용.
   - `SPRING_INITIALIZR_DEPENDENCIES.md` 삭제 확인.

3. Real build check:
   - 최소 dependency 선택 없이 생성 후 build.
   - `webflux`, `validation`, `configuration-processor`, `jooq`, `h2` 등 skeleton에 필요한 dependency 선택/자동 추가 후 build.
   - Boot stable 버전과 milestone/snapshot 버전은 가능하면 분리 검증.

4. Skill validation:
   - `quick_validate.py <skill-folder>`.
   - Forward-test prompt:
     ```text
     Use $springboot-kotlin-initializr to create a new project in this empty folder.
     ```
   - Forward-test prompt:
     ```text
     Use $springboot-kotlin-initializr to generate a dependency checklist for boot=default, java=default, kotlin=default, artifact=default, group=com.example.
     ```

## Open Questions

1. 스킬 이름을 `springboot-kotlin-initializr`로 진행해도 되는가?
2. 스킬 생성 위치는 이전처럼 `./skills`인가, 아니면 `${CODEX_HOME:-$HOME/.codex}/skills`인가?
3. Artifact에 hyphen이 들어올 때 `{group}.{artifact}` 고정 정책을 엄격히 적용해 에러로 멈출지, package segment만 normalize할지 결정이 필요하다.
4. Skeleton overlay에서 WebFlux/jOOQ 관련 필수 dependency를 사용자가 선택하지 않았을 경우 자동 추가할지, 사용자에게 확인받을지 결정이 필요하다.
