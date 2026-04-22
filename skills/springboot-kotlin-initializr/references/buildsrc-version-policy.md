# buildSrc Version Policy

Spring Initializr가 생성한 Gradle version literal은 생성 직후 `buildSrc`로 이동한다. Skeleton source를 지정하지 않는 경우에도 `https://github.com/moohee-lee/springboot-kotlin-skeleton`와 같은 `buildSrc` 구조를 만든다.

## 파일 구조

```text
buildSrc/
└── src/main/kotlin/
    ├── BuildVersions.kt
    ├── PluginVersions.kt
    └── DependencyVersions.kt
```

## 역할

- `BuildVersions.kt`: Java toolchain/JVM target.
- `PluginVersions.kt`: Kotlin, Spring Boot, dependency-management, detekt, jOOQ plugin version.
- `DependencyVersions.kt`: Spring Boot BOM이 관리하지 않는 외부 library version.

## 규칙

- 사용자 입력 또는 Initializr 선택 결과로 확정된 `SPRING_BOOT`, `KOTLIN`, `JAVA`, `group`, `artifact`는 불변 입력이다. 사용자가 명시적으로 다시 선택하지 않는 한 수정하지 않는다.
- Spring Boot BOM/dependency-management가 관리하는 dependency에는 version을 직접 쓰지 않는다.
- Gradle plugin version은 `PluginVersions`에 둔다.
- Java version은 `BuildVersions`에 둔다.
- 직접 버전이 필요한 외부 library만 `DependencyVersions`에 둔다.
- `build.gradle.kts`에 같은 version string을 두 번 이상 반복하지 않는다.
- 사용자가 Kotlin version을 직접 지정하면 `PluginVersions.KOTLIN` 값을 사용자 지정값으로 둔다.
- Initializr가 생성한 Kotlin/Spring Boot/dependency-management plugin version은 skeleton version보다 우선한다.
- Skeleton source가 없으면 skeleton 저장소의 기본 상수 이름과 구조를 사용하고, Initializr가 생성한 Kotlin/Spring Boot/dependency-management/Java version으로 값을 덮어쓴다.
- Skeleton source가 있으면 source의 `buildSrc`를 복사하되, Initializr가 생성한 Kotlin/Spring Boot/dependency-management/Java version으로 값을 덮어쓴다.
- 빌드 도구 호환성 오류를 해결하기 위해 사용자 선택 Kotlin/Spring Boot/Java 버전을 낮추거나 올리지 않는다. detekt, jOOQ, Gradle plugin, test tool 같은 문제는 해당 도구 버전/설정/classpath를 공식 문서 기준으로 조정한다.

## 도구 호환성 대응 원칙

빌드 실패 원인이 특정 도구나 plugin이면 다음 순서를 따른다.

1. 실패 로그에서 도구 이름, plugin 이름, 실제 실행 version, 기대 version을 확인한다.
2. 해당 도구의 공식 문서를 찾아 compatibility table, migration guide, Gradle integration 문서를 확인한다.
3. 사용자 선택값(`KOTLIN`, `SPRING_BOOT`, `JAVA`)을 변경하지 않는 해결책을 먼저 적용한다.
4. 해결책이 사용자 선택값 변경뿐이라면 중단하고 사용자에게 trade-off를 보고한다.

Detekt 예:

- detekt는 Kotlin compiler와 강하게 결합되어 있으므로 Kotlin compiler mismatch가 발생할 수 있다.
- 이때 `PluginVersions.KOTLIN`을 detekt에 맞춰 낮추지 않는다.
- detekt 공식 compatibility table에서 선택 Kotlin/Gradle/JDK에 맞는 detekt version을 찾거나, detekt Gradle runtime dependency 문서에 따라 detekt configuration의 Kotlin compiler classpath가 잘못 override되는지 확인한다.
- 조정 대상은 `PluginVersions.DETEKT`, `detektPlugins(...)`, `configurations.matching { it.name.startsWith("detekt") }` 같은 detekt 전용 설정이다.

## 예시

```kotlin
import org.gradle.api.JavaVersion

object BuildVersions {
    val JAVA = JavaVersion.VERSION_25
}
```

```kotlin
object PluginVersions {
    const val DETEKT = "2.0.0-alpha.2"
    const val KOTLIN = "2.2.21"
    const val SPRING_BOOT = "4.0.5"
    const val SPRING_DEPENDENCY_MANAGEMENT = "1.1.7"
    const val JOOQ = "3.19.31"
    const val JIB = "3.5.2"
}
```

```kotlin
object DependencyVersions {
    const val SPRING_RESTDOCS_WEBTESTCLIENT = "4.0.0"
    const val MOCKK = "1.14.9"
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
