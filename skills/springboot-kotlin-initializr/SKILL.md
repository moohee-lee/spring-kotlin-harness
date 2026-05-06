---
name: springboot-kotlin-initializr
description: Spring Initializr로 Spring Boot Kotlin 프로젝트를 생성하고 사용자가 지정한 skeleton GitHub repo 또는 local directory의 공통 아키텍처/설정 구조를 적용하는 스캐폴딩 워크플로우. Spring Boot Kotlin 신규 프로젝트 생성, Initializr metadata 추천값 조회, dependency 체크박스 선택 파일 생성/파싱, Gradle-Kotlin/Jar/YAML 고정 생성, skeleton source 미지정 시에도 buildSrc 기반 버전 관리 적용, skeleton common/config/resources/transaction/persistence overlay, 최종 Gradle 빌드 검증이 필요할 때 사용한다.
---

# Spring Boot Kotlin Initializr

이 스킬은 Spring Initializr로 Spring Boot Kotlin 프로젝트를 만든 뒤 사용자가 지정한 skeleton source의 공통 구조를 적용한다. Skeleton source는 GitHub repository URL, GitHub archive URL, 또는 local directory일 수 있다.

고정 Initializr 값:

- `type=gradle-project-kotlin`
- `language=kotlin`
- `packaging=jar`
- `configurationFileFormat=yaml`

사용자 입력 형식:

```text
boot=<boot-version>, java=<java-version>, kotlin=default, artifact=default, group=com.example
```

누락되거나 `default`인 값은 Initializr 기본값을 사용한다. `artifact=default`는 현재 폴더명을 사용한다. `packageName`은 항상 `{group}.{artifact}`로 만든다. 현재 폴더명이 Kotlin package segment로 유효하지 않으면 `artifact=default`를 사용할 수 없으므로, 반드시 형식에 맞는 `artifact=<valid-name>`을 사용자에게 입력받은 뒤 진행한다.

## 워크플로우

1. 추천값을 조회한다.
   ```bash
   python3 <skill-dir>/scripts/initializr_metadata.py --project-root .
   ```
   출력된 Boot/Java/Kotlin/Artifact 추천값을 사용자에게 보여주고 입력 형식으로 답을 요청한다.
   현재 폴더명에 하이픈 등 package segment로 부적합한 문자가 있으면 metadata 스크립트가 `artifact=default` 사용 불가와 추천 artifact 값을 출력한다. 이 경우 사용자가 명시적인 `artifact=<valid-name>`을 제공할 때까지 다음 단계로 진행하지 않는다.

2. 사용자 입력을 받은 뒤 dependency 체크박스 파일을 만든다.
   ```bash
   python3 <skill-dir>/scripts/write_dependency_checklist.py \
     --project-root . \
     --request "boot=default, java=default, kotlin=default, artifact=default, group=com.example"
   ```
   생성된 `SPRING_INITIALIZR_DEPENDENCIES.md`를 사용자가 수정하도록 안내한다.

3. 사용자가 체크박스 수정을 완료했다고 하면 선택값을 파싱한다.
   ```bash
   python3 <skill-dir>/scripts/parse_dependency_checklist.py \
     --checklist SPRING_INITIALIZR_DEPENDENCIES.md \
     --selection-json /tmp/spring-initializr-selection.json
   ```

4. Initializr 프로젝트를 생성한다.
   ```bash
   python3 <skill-dir>/scripts/create_initializr_project.py \
     --selection-json /tmp/spring-initializr-selection.json \
     --target-dir .
   ```
   성공하면 `SPRING_INITIALIZR_DEPENDENCIES.md`를 삭제한다. 이 단계는 skeleton source 지정 여부와 무관하게 `https://github.com/moohee-lee/springboot-kotlin-skeleton`의 `buildSrc` 구조를 따라 Gradle version literal을 `buildSrc`의 `BuildVersions`, `PluginVersions`, `DependencyVersions`로 이동한다.
   사용자가 `boot`, `java`, `kotlin`을 명시하면 Initializr가 생성한 값보다 사용자 요청값을 우선한다. Initializr가 다른 값을 생성하면 스크립트가 `WARN`을 출력하며, 빌드 검증에서 Gradle/Spring Boot/Kotlin/Java 정합성 문제가 드러나면 사용자에게 선택지를 확인한 뒤 진행한다.

5. Skeleton overlay 여부를 확인한다.
   Overlay 전에 사용자에게 skeleton source를 물어본다. 사용자가 skeleton source가 없다고 하거나 `none`, `skip`, `initializr-only`로 답하면 overlay를 건너뛰고 Initializr 프로젝트와 `buildSrc` 기반 version 관리가 적용된 상태로 종료한다.
   ```text
   skeleton-source=<github-repo-or-local-directory|none>, skeleton-ref=main
   ```
   `skeleton-ref`는 GitHub repository URL일 때만 사용하며 생략 시 `main`이다.

   ```bash
   python3 <skill-dir>/scripts/apply_skeleton_overlay.py \
     --selection-json /tmp/spring-initializr-selection.json \
     --project-root . \
     --skeleton-source "<github-repo-or-local-directory>" \
     --skeleton-ref main
   ```
   Skeleton source가 제공되면 sample domain 파일을 제외하고 `common`, `buildSrc`, config/resources, transaction/persistence 기반 구조를 대상 package로 변환한다. WebFlux/jOOQ/validation/configuration-processor 등 skeleton 필수 dependency는 선택되지 않았어도 자동 추가한다.
   Skeleton source가 없으면 다음 안내를 사용자에게 명확히 보여준다: "Spring Initializr 프로젝트 생성과 buildSrc 기반 Gradle 버전 관리는 완료되었고 skeleton 공통 구조는 적용되지 않았습니다."

6. 빌드 검증을 실행한다.
   ```bash
   ./gradlew build
   ```
   jOOQ 설정이 적용된 경우 필요하면 먼저 `./gradlew jooqCodegen` 또는 `./gradlew compileKotlin`으로 좁게 확인한다.
   빌드가 실패하면 실패한 도구/플러그인의 공식 문서를 먼저 확인하고 대응한다. 사용자가 선택한 Spring Boot, Java, Kotlin, Group, Artifact 값은 오류 해결을 위해 임의로 바꾸지 않는다. 요청한 버전 조합 자체가 Gradle/Spring Boot/Kotlin/Java 정합성을 깨뜨리는 것으로 확인되면 멈추고 사용자에게 어떤 버전을 조정할지 확인한다.

## 레퍼런스

- `references/initializr-flow.md`: Initializr metadata/dependencies/starter.zip API 흐름.
- `references/dependency-selection.md`: `SPRING_INITIALIZR_DEPENDENCIES.md` 생성/파싱 규칙.
- `references/skeleton-overlay.md`: skeleton 적용/제외 대상과 package 변환 규칙.
- `references/buildsrc-version-policy.md`: Initializr 생성 버전을 `buildSrc`로 옮기는 정책.
- `references/verification.md`: 생성 후 검증 체크리스트와 실패 대응.

## 안전 규칙

- 비어 있지 않은 디렉터리에도 생성될 파일/디렉터리 경로와 충돌이 없으면 진행한다.
- 생성될 경로가 기존 파일을 덮어쓰거나, 기존 파일 위치에 디렉터리를 만들어야 하는 경우에만 충돌 목록을 보고하고 사용자 승인을 받는다.
- 사용자가 만든 기존 파일은 명시 승인 없이 삭제하지 않는다.
- `SPRING_INITIALIZR_DEPENDENCIES.md`만 생성 산출물로 취급하고, 프로젝트 생성 성공 후 삭제한다.
- Initializr metadata와 실제 생성된 `build.gradle.kts`가 다를 수 있으므로 생성 후 plugin/java version을 다시 확인한다.
- 사용자가 명시한 `boot`, `java`, `kotlin`은 생성 후 `buildSrc`에 그대로 반영한다. Initializr가 더 낮거나 다른 값을 생성해도 요청값을 자동으로 낮추지 않는다.
- Spring Boot BOM이 관리하는 dependency에는 직접 버전을 붙이지 않는다. 직접 버전이 필요한 값만 `buildSrc`의 `PluginVersions`, `DependencyVersions`, `BuildVersions`로 옮긴다.
- 사용자 선택값은 불변 입력으로 취급한다. `boot`, `java`, `kotlin`, `group`, `artifact`는 사용자가 다시 지시하지 않는 한 빌드 오류 해결 과정에서 수정하지 않는다.
- 도구 호환성 문제는 해당 도구 쪽을 조정한다. 예를 들어 detekt가 Kotlin compiler version 불일치로 실패하면 Kotlin 버전을 낮추지 말고 detekt 공식 compatibility/runtime 문서를 확인한 뒤 detekt plugin version, detekt classpath, detekt 전용 `resolutionStrategy`, detekt 실행 제외/보류 여부를 검토한다.
- Skeleton source는 고정값으로 가정하지 않는다. 사용자가 제공한 `skeleton-source`만 사용한다. 제공되지 않거나 사용자가 없다고 답하면 overlay를 건너뛰고 Spring Initializr 생성 상태로 종료할 수 있음을 안내한다.
