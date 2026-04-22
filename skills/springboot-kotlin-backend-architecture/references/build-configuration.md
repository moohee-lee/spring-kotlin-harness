# Build Configuration 레퍼런스

대상 프로젝트의 Gradle Kotlin DSL 규칙을 따른다. Skeleton 스타일에서는 버전을 `buildSrc`로 중앙 관리한다. 이미 version catalog를 표준으로 쓰는 프로젝트라면 기존 표준을 따르되, 이 스킬의 기본 지침은 `buildSrc` 기반이다.

## 의존성 범주

Skeleton 스타일 전체 스택에는 다음 범주의 의존성이 필요하다.

- Spring Boot WebFlux.
- Spring Boot Validation.
- Spring Boot jOOQ.
- 대상 Spring Boot 버전에 맞는 Spring WebClient / HTTP client 지원.
- Kotlin reflection.
- Kotlin coroutine Reactor bridge.
- 필요한 경우 Reactor Kotlin extensions.
- Jackson Kotlin module.
- Trace ID MDC 전파를 위한 Micrometer context propagation.
- Runtime database driver.
- DDL 기반 jOOQ generation을 사용하는 경우 codegen database driver와 metadata extension.
- Spring Boot test starter.
- Kotlin test/JUnit 5.
- Coroutine test utilities.
- Reactor test.
- MockK 또는 프로젝트의 mocking standard.
- detekt 기반 정적 분석을 쓰는 경우 detekt와 ktlint wrapper.

## buildSrc 버전 관리 규칙

특정 버전을 명시해야 하는 의존성이나 plugin을 추가할 때는 `build.gradle.kts`에 버전 문자열을 직접 쓰지 않는다. `buildSrc`의 상수로 분리하고 Gradle 파일에서는 상수를 참조한다.

권장 구조:

```text
buildSrc/
└── src/main/kotlin/
    ├── BuildVersions.kt
    ├── PluginVersions.kt
    └── DependencyVersions.kt
```

역할:

- `BuildVersions.kt`: Java toolchain, JVM target처럼 build runtime과 관련된 버전.
- `PluginVersions.kt`: Kotlin, Spring Boot, dependency-management, detekt, jOOQ Gradle plugin 같은 plugin version.
- `DependencyVersions.kt`: MockK, 별도 BOM이 관리하지 않는 library, annotation processor extension, codegen helper처럼 직접 버전 지정이 필요한 dependency version.

예시:

```kotlin
// buildSrc/src/main/kotlin/DependencyVersions.kt
object DependencyVersions {
    const val MOCKK = "1.14.9"
    const val CUSTOM_CLIENT = "2.3.1"
}
```

```kotlin
// build.gradle.kts
dependencies {
    testImplementation("io.mockk:mockk:${DependencyVersions.MOCKK}")
    implementation("com.example:custom-client:${DependencyVersions.CUSTOM_CLIENT}")
}
```

Plugin version 예시:

```kotlin
// buildSrc/src/main/kotlin/PluginVersions.kt
object PluginVersions {
    const val KOTLIN = "2.3.20"
    const val SPRING_BOOT = "4.0.5"
    const val DETEKT = "2.0.0-alpha.2"
    const val JOOQ = "3.19.31"
}
```

```kotlin
plugins {
    kotlin("jvm") version PluginVersions.KOTLIN
    kotlin("plugin.spring") version PluginVersions.KOTLIN
    id("org.springframework.boot") version PluginVersions.SPRING_BOOT
    id("dev.detekt") version PluginVersions.DETEKT
    id("org.jooq.jooq-codegen-gradle") version PluginVersions.JOOQ
}
```

판단 기준:

- Spring Boot BOM/dependency-management가 관리하는 `org.springframework.boot:*`, Jackson, Reactor 등은 보통 버전을 생략한다.
- BOM이 관리하지 않거나 프로젝트에서 고정해야 하는 외부 라이브러리는 `DependencyVersions`에 상수를 추가한다.
- Gradle plugin version은 `PluginVersions`에 둔다.
- Java version/JVM target은 `BuildVersions`에 둔다.
- 같은 버전 문자열을 두 곳 이상 반복하지 않는다.
- 새 상수를 추가하면 이름은 dependency 목적이 드러나게 대문자 snake case로 짓는다.

## Configuration Processor

프로젝트가 `@ConfigurationProperties`를 사용하면 Spring Boot configuration processor를 추가한다.

```kotlin
configurations {
    compileOnly {
        extendsFrom(configurations.annotationProcessor.get())
    }
}

dependencies {
    annotationProcessor("org.springframework.boot:spring-boot-configuration-processor")
}
```

Kotlin KAPT/KSP 기반 프로젝트라면 프로젝트의 annotation-processing 설정에 맞게 조정한다. Spring Boot BOM이 관리하는 경우 configuration processor 버전은 직접 쓰지 않는다.

## Compiler And Toolchain

대상 프로젝트의 Java/Kotlin 버전을 사용한다. 레퍼런스 버전을 강제하지 않는다.

호환되는 경우 권장 compiler option:

```kotlin
kotlin {
    compilerOptions {
        freeCompilerArgs.addAll(
            "-Xjsr305=strict",
            "-Xannotation-default-target=param-property",
        )
    }
}
```

`jvmToolchain`과 `jvmTarget`은 대상 프로젝트의 기존 규칙을 따른다. Skeleton 스타일에서는 `BuildVersions.JAVA` 같은 buildSrc 상수를 참조한다.

## jOOQ Build Integration

Generated jOOQ source를 사용할 때는 다음을 지킨다.

- `build` 아래에 generated source directory를 정의한다.
- jOOQ generator package는 대상 base package 아래로 설정한다.
- Generated source를 Kotlin main source set에 추가한다.
- `compileKotlin`이 `jooqCodegen`에 의존하도록 한다.
- Generated source는 detekt/static analysis 대상에서 제외한다.
- jOOQ Gradle plugin version은 `PluginVersions.JOOQ` 같은 buildSrc 상수로 관리한다.

## 정적 분석

detekt를 사용한다면 다음을 지킨다.

- 설정은 `config/detekt/detekt.yml` 아래에 둔다.
- 프로젝트에 더 엄격한 표준이 없다면 `buildUponDefaultConfig = true`를 사용한다.
- 안정적으로 동작하면 parallel execution을 켠다.
- `build`와 generated jOOQ source는 제외한다.
- CI에 맞는 Markdown 또는 CI-friendly report를 사용한다.

레퍼런스의 formatting convention:

- IntelliJ-compatible ktlint style.
- 120자 max line length.
- 프로젝트 스타일이 허용하면 declaration site trailing comma.

대상 repository의 formatter가 이미 다르면 기존 formatter를 따른다.

## 검증 명령

대상 repository에서 제공하는 명령을 사용한다. 일반적인 명령:

```bash
./gradlew jooqCodegen
./gradlew compileKotlin
./gradlew test
./gradlew detekt
./gradlew build
```

작업 중에는 좁은 명령부터 실행하고, 마무리 전에 더 넓은 build/check 명령을 실행한다.
