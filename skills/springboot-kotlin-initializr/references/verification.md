# Verification

## 생성 직후 확인

- `SPRING_INITIALIZR_DEPENDENCIES.md`가 프로젝트 생성 성공 후 삭제되었다.
- 생성 대상 디렉터리에 기존 파일/디렉터리가 있어도 생성 산출물과 경로 충돌이 없으면 유지되었다.
- 생성 산출물이 기존 파일을 덮어쓸 상황에서는 생성이 중단되고 충돌 경로가 보고되었다.
- `application.yaml`이 존재한다.
- `application.properties`가 생성되지 않았거나 사용되지 않는다.
- `packageName`이 `{group}.{artifact}`와 일치한다.
- 현재 폴더명이 package segment로 유효하지 않은 경우 `artifact=default`로 진행되지 않고, 명시적인 유효 artifact 입력을 요구한다.
- Main application class의 package declaration과 파일 경로가 일치한다.
- `settings.gradle.kts`의 root project name이 artifact와 일치한다.

## Skeleton overlay 확인

- Overlay 전에 사용자가 skeleton source 제공 여부를 선택했다.
- Skeleton source가 없으면 overlay가 건너뛰어졌고, Spring Initializr 프로젝트와 `buildSrc` 기반 version 관리는 생성되었지만 skeleton 공통 구조는 적용되지 않았다는 안내가 출력되었다.
- Local directory를 제공한 경우 해당 경로가 존재한다.
- GitHub repo URL을 제공한 경우 지정한 `skeleton-ref` archive를 내려받을 수 있다.
- `buildSrc`가 존재하고 `BuildVersions`, `PluginVersions`, `DependencyVersions`가 있다.
- `common` package가 target package 아래에 있다.
- `adapter/output/transaction`, `application/port/output/transaction`이 target package 아래에 있다.
- `adapter/output/persistence/config`가 target package 아래에 있다.
- `resources/errors`, `resources/enums`, `resources/messages`, `resources/validations`가 있다.
- sample domain/API/test 파일이 남지 않았다.
- `com.example.skeleton` import/package가 남지 않았다.

## Build 확인

우선 좁은 명령부터 실행한다.

```bash
./gradlew compileKotlin
```

Sandbox나 CI에서 Gradle/Kotlin cache 위치가 제한되면 repository 내부 cache를 사용한다.

```bash
env GRADLE_USER_HOME=.gradle-user-home ./gradlew compileKotlin --no-daemon
```

jOOQ 설정이 적용된 경우:

```bash
./gradlew jooqCodegen
```

마지막에 전체 빌드를 실행한다.

```bash
./gradlew build
```

## 실패 대응

- Initializr 다운로드 실패: metadata endpoint와 starter.zip URL, network 상태를 확인한다.
- Java version mismatch: 생성된 `build.gradle.kts`의 `JavaLanguageVersion.of(...)`와 사용자 입력을 비교해 보고한다.
- Kotlin plugin mismatch: probe 결과와 생성 결과를 비교한다.
- BuildSrc 인식 실패: `buildSrc/build.gradle.kts`와 Kotlin source 위치를 확인한다.
- Missing dependency: `/dependencies?bootVersion=...` resolved map에서 dependency id가 제공되는지 확인한다.
- Package compile error: `com.example.skeleton` 잔여 import와 target package path를 검색한다.

## 실패 대응 원칙

- 사용자가 선택한 Spring Boot, Java, Kotlin, Group, Artifact 값은 빌드 오류 해결 과정에서 임의 변경하지 않는다.
- 실패한 대상이 Gradle plugin, detekt, jOOQ, Kotlin compiler plugin, test framework, dependency-management라면 해당 도구의 공식 문서를 먼저 확인한다.
- 공식 문서 확인 없이 "Kotlin을 낮추기", "Spring Boot를 낮추기", "Java를 바꾸기" 같은 선택값 변경을 하지 않는다.
- 공식 문서 기반 조정으로 해결할 수 없으면 중단하고 사용자에게 선택지를 제시한다.

### detekt 실패 예시

증상:

```text
detekt was compiled with Kotlin X but is currently running with Y
```

처리:

1. detekt 공식 compatibility table에서 현재 detekt version이 어떤 Kotlin/Gradle/JDK 조합으로 컴파일/검증되었는지 확인한다.
2. detekt Gradle runtime dependency 공식 문서에서 detekt classpath의 Kotlin compiler가 dependency-management나 global resolutionStrategy로 override되고 있는지 확인한다.
3. 사용자 선택 `PluginVersions.KOTLIN`은 변경하지 않는다.
4. 필요하면 detekt 전용으로 다음 중 하나를 적용한다.
   - `PluginVersions.DETEKT`를 공식 compatibility에 맞는 버전으로 조정.
   - `detektPlugins(...)` 버전을 `PluginVersions.DETEKT`와 맞춤.
   - Kotlin dependency alignment가 있다면 detekt configuration에는 적용하지 않도록 제외.
   - detekt가 아직 선택 Kotlin을 지원하지 않으면 사용자에게 detekt 보류/제거/버전 변경 선택지를 제시.
