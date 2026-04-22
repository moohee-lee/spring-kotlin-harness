# Initializr Flow

## Metadata 조회

Spring Initializr metadata를 조회해 사용 가능한 Boot version, Java version, dependency category, generation link를 확인한다.

```http
GET https://start.spring.io/metadata/client
Accept: application/vnd.initializr.v2.3+json
User-Agent: codex-springboot-kotlin-initializr/1.0
```

Metadata에서 확인할 값:

- `bootVersion.values`
- `javaVersion.values`
- `language.values` 중 `kotlin`
- `type.values` 중 `gradle-project-kotlin`
- `packaging.values` 중 `jar`
- `configurationFileFormat.values` 중 `yaml`
- `_links.gradle-project-kotlin.href`
- `_links.dependencies.href`

## 추천값 표시

사용자에게 다음 형태로 추천값을 보여준다.

```text
추천 생성 값
- Spring Boot: 4.0.5
- Java: 17 (Initializr default)
- Kotlin: Spring Boot 4.0.5 생성 기본값은 2.2.21
- Artifact 기본값: 현재 폴더명

입력 형식:
boot=<boot-version>, java=<java-version>, kotlin=default, artifact=default, group=com.example
```

Kotlin version은 metadata가 직접 제공하지 않을 수 있다. 이 경우 선택한 Boot/Java 조건으로 probe project 또는 build file을 생성해 `kotlin("jvm") version` 값을 읽는다.

Artifact 기본값은 현재 폴더명이다. 현재 폴더명이 Kotlin package segment 형식(`^[A-Za-z_][A-Za-z0-9_]*$`)을 만족하지 않으면 `artifact=default`를 사용할 수 없다. 이 경우 추천값 출력 단계는 실패하지 말고 다음을 명확히 안내한다.

- 현재 폴더명은 artifact 기본값으로 사용할 수 없음.
- 반드시 `artifact=<valid-name>`을 직접 입력해야 함.
- 하이픈 제거 등으로 만든 추천값 예시.

## Dependency resolution 조회

사용자가 선택한 Boot version으로 dependency resolution endpoint를 조회한다.

```http
GET https://start.spring.io/dependencies?bootVersion=<boot>
```

이 응답은 dependency id별 `groupId`, `artifactId`, `scope`, 필요한 BOM, repository를 제공한다. Dependency checklist는 이 resolved map에 존재하는 항목만 기본 표시한다.

## Project 생성

`starter.zip`으로 프로젝트를 생성한다.

고정 파라미터:

- `type=gradle-project-kotlin`
- `language=kotlin`
- `packaging=jar`
- `configurationFileFormat=yaml`

사용자/파생 파라미터:

- `bootVersion=<boot>`: 사용자가 `default`가 아닌 값을 선택한 경우만 전달한다.
- `javaVersion=<java>`: 사용자가 `default`가 아닌 값을 선택한 경우만 전달한다.
- `groupId=<group>`
- `artifactId=<artifact>`
- `name=<artifact>`
- `packageName=<group>.<artifact>`
- `dependencies=<comma-separated dependency ids>`

`kotlin=default`이면 Initializr가 생성한 Kotlin plugin version을 유지한다. 사용자가 Kotlin version을 명시하면 생성 후 `buildSrc/PluginVersions.kt`와 `build.gradle.kts`에 반영한다.

`create_initializr_project.py`는 skeleton source가 아직 지정되지 않았더라도 생성 직후 Gradle version literal을 `buildSrc`로 이동한다. 기본 구조는 `https://github.com/moohee-lee/springboot-kotlin-skeleton`와 같은 형태를 따른다.

- `buildSrc/build.gradle.kts`: `kotlin-dsl` plugin과 `mavenCentral()`.
- `buildSrc/src/main/kotlin/BuildVersions.kt`: `JavaVersion.VERSION_<java>` 형식의 `JAVA`.
- `buildSrc/src/main/kotlin/PluginVersions.kt`: Kotlin, Spring Boot, dependency-management와 skeleton 기본 plugin version 상수.
- `buildSrc/src/main/kotlin/DependencyVersions.kt`: Spring Boot BOM이 관리하지 않는 skeleton 기본 library version 상수.

Skeleton source를 나중에 제공하면 overlay 단계에서 skeleton source의 `buildSrc`를 복사하되, Initializr가 생성한 Kotlin/Spring Boot/dependency-management/Java version은 유지한다.

대상 디렉터리가 비어 있지 않아도 생성될 zip entry와 기존 경로가 충돌하지 않으면 그대로 진행한다. 기존 파일을 덮어쓰는 경우, 또는 기존 파일 위치에 생성 디렉터리가 필요한 경우에만 중단하고 충돌 목록을 보고한다.

## 생성 후 검증

Initializr가 요청값을 조정할 수 있으므로 생성된 `build.gradle.kts`를 확인한다.

- `kotlin("jvm") version`
- `kotlin("plugin.spring") version`
- `id("org.springframework.boot") version`
- `id("io.spring.dependency-management") version`
- `JavaLanguageVersion.of(...)`
- `application.yaml` 생성 여부
- package path와 package declaration
