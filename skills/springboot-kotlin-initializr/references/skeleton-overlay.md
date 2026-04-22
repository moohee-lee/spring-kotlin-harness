# Skeleton Overlay

Overlay 기준 source는 사용자에게 입력받는다.

```text
skeleton-source=<github-repo-or-local-directory|none>, skeleton-ref=main
```

지원 형식:

- GitHub repository URL: `https://github.com/owner/repo`
- GitHub branch/tag URL: `https://github.com/owner/repo/tree/<ref>`
- GitHub archive URL: `https://github.com/owner/repo/archive/refs/heads/main.zip`
- Local directory: `/path/to/springboot-kotlin-skeleton`
- 없음: `none`, `skip`, `initializr-only`

`skeleton-ref`는 GitHub repository URL일 때만 사용한다. Local directory나 archive URL이면 무시한다.

Skeleton source가 없으면 overlay를 건너뛰고 정상 종료한다. 이때 사용자에게 다음 사실을 안내한다.

- Spring Initializr 프로젝트 생성과 `buildSrc` 기반 Gradle version 관리는 완료되었다.
- Skeleton source의 `common`, `config`, `resources`, `transaction`, `persistence` 구조와 source-specific `buildSrc` override는 적용되지 않았다.
- 나중에 skeleton source를 지정해 overlay 스크립트를 다시 실행할 수 있다.

## 적용 대상

다음 파일/디렉터리를 target package로 변환해 적용한다.

- `buildSrc/`
- `config/detekt/`
- `src/main/kotlin/com/example/skeleton/common/**`
- `src/main/kotlin/com/example/skeleton/adapter/output/persistence/config/DatabasePersistenceConfiguration.kt`
- `src/main/kotlin/com/example/skeleton/adapter/output/transaction/TransactionalExecutorAdapter.kt`
- `src/main/kotlin/com/example/skeleton/application/port/output/transaction/TransactionalPort.kt`
- `src/main/resources/errors/error.properties`에서 common error만
- `src/main/resources/enums/enum.properties`는 sample enum 제거 후 placeholder 유지
- `src/main/resources/messages/message.properties`
- `src/main/resources/validations/validation.properties`
- `src/main/resources/db/schema.sql`은 sample table 제거 후 placeholder 유지
- `src/test/resources/application-test.yml` if datasource/test setup is applied

## 제외 대상

예시 domain/API 파일은 복사하지 않는다.

- `domain/sample/**`
- `application/port/input/sample/**`
- `application/port/output/sample/**`
- `application/service/SampleService.kt`
- `adapter/input/web/sample/**`
- `adapter/output/persistence/jooq/sample/**`
- `common/errors/SampleErrorCode.kt`
- `common/exception/SampleNotFoundException.kt`
- sample 관련 test files
- `README.md`, `HELP.md`, sample API 문서

Overlay 후 `sample`, `Sample`, `SAMPLE_` 잔여물을 검색한다. Common error 메시지의 `sample`은 제거되어야 한다.

## Package 변환

Skeleton source package:

```text
com.example.skeleton
```

Target package:

```text
{group}.{artifact}
```

경로와 package/import 선언을 모두 변환한다.

Artifact는 package segment로 유효해야 한다. `my-service`처럼 hyphen이 포함되면 `{group}.{artifact}` 고정 정책을 만족할 수 없으므로 중단하고 사용자에게 artifact 수정을 요청한다.

## Build merge

Initializr가 생성한 wrapper, `settings.gradle.kts`, application class, 기본 test class는 유지한다.

`build.gradle.kts`는 Initializr 결과를 source of truth로 삼고 다음만 병합한다.

- `buildSrc` 상수 기반 plugin version 참조.
- detekt plugin/config.
- jOOQ codegen plugin/config if skeleton persistence support is applied.
- skeleton common에 필요한 dependency.
- configuration processor 설정.
- generated jOOQ source set 등록.

Skeleton의 Java/Kotlin/Spring Boot 버전을 그대로 강제하지 않는다. Initializr가 생성한 값 또는 사용자가 지정한 값을 `buildSrc`로 이동한다.

## Java version adaptation

Skeleton의 transaction/persistence 예시는 Java 21+ virtual thread API를 사용한다.

대상 Java version이 21 미만이면 overlay 스크립트는 다음을 자동 보정한다.

- `Executors.newVirtualThreadPerTaskExecutor()`를 bounded fixed thread pool로 바꾼다.
- `Thread.currentThread().isVirtual` 로그 인자를 Java 17에서도 컴파일 가능한 값으로 바꾼다.

Java 21 이상이면 skeleton의 virtual thread 구현을 유지한다.

## Source validation

사용자 지정 skeleton source는 다음 구조를 가져야 한다.

- `src/main/kotlin/<source-package>/common`
- `buildSrc` 또는 build version 정보를 추출할 수 있는 Gradle 설정
- `src/main/resources/errors`, `validations`, `messages`

현재 overlay 스크립트는 source package를 `com.example.skeleton`으로 가정한다. 다른 source package를 가진 skeleton을 지원해야 하면 `--source-package` 옵션을 추가하는 개선이 필요하다.
