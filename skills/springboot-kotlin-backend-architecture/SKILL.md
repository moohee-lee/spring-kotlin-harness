---
name: springboot-kotlin-backend-architecture
description: Spring Boot Kotlin 백엔드 개발과 리뷰를 springboot-kotlin-skeleton 레퍼런스 기반의 버전 독립적인 Hexagonal Architecture 지침으로 안내한다. Spring Boot Kotlin 프로젝트 생성/수정, 신규 도메인 추가, adapter/application/domain/common 패키지 경계 유지, WebFlux coroutine API, validation, i18n message resolution, ErrorCode/exception 기반 에러 처리, WebClient, jOOQ, read/write datasource routing, transaction execution, Gradle Kotlin DSL, buildSrc 기반 버전 관리, spring-boot-configuration-processor 설정 작업에 사용한다.
---

# Spring Boot Kotlin Backend Architecture

이 스킬은 Spring Boot Kotlin 백엔드를 skeleton 스타일의 Hexagonal Architecture + DDD 패키지 구조로 개발하거나 리뷰할 때 사용한다.

레퍼런스 저장소는 `https://github.com/moohee-lee/springboot-kotlin-skeleton`이다. 저장소에 적힌 Java, Kotlin, Spring Boot, Gradle, jOOQ 버전은 예시로만 취급한다. 대상 프로젝트의 실제 버전에 맞춰 API 이름, Gradle 플러그인, 의존성 좌표, 설정 방식을 조정한다.

## 작업 흐름

1. 수정 전에 대상 프로젝트를 먼저 확인한다.
   - base package, Gradle 구조, Spring Boot/Kotlin 버전, WebFlux/MVC 선택, persistence 방식, 기존 패키지 규칙을 파악한다.
   - 대상 프로젝트가 WebFlux나 jOOQ 기반이 아니어도 계층 경계는 유지하고, transport/persistence 세부 구현만 실제 스택에 맞춘다.

2. 의존성 방향을 지킨다.
   - `adapter`는 `application`, `domain`, `common`에 의존할 수 있다.
   - `application`은 `domain`, 자기 계층의 port, 안정적인 common 유틸리티에 의존할 수 있다.
   - `domain`은 framework-light하게 유지하고 WebFlux, jOOQ, database record, request DTO, Spring configuration에 의존하지 않는다.
   - concrete adapter는 output port를 구현하고, service는 adapter class가 아니라 port에 의존한다.

3. 도메인 추가/수정은 표준 경로로 진행한다.
   - domain model/enum을 먼저 정의한다.
   - input port/use case와 command/query model을 추가한다.
   - output port interface를 추가한다.
   - application service를 구현한다.
   - inbound web router/handler와 request/response protocol DTO를 추가한다.
   - 필요하면 outbound persistence adapter, schema, jOOQ 생성 설정을 갱신한다.
   - domain error code와 i18n message를 등록한다.

4. 공통 인프라는 도메인마다 복제하지 말고 `common`을 재사용한다.
   - cross-cutting configuration, error response type, validation helper, enum helper, trace ID 처리, message conversion은 `common` 아래에 둔다.
   - domain-specific business rule, query, policy는 `common`에 넣지 않는다.

5. Gradle 의존성을 추가할 때 버전 정책을 지킨다.
   - Spring Boot BOM/dependency-management가 관리하는 의존성은 가능하면 버전을 직접 쓰지 않는다.
   - 특정 버전을 직접 지정해야 하는 외부 라이브러리, Gradle plugin, codegen dependency는 `buildSrc`의 `DependencyVersions`, `PluginVersions`, `BuildVersions` 같은 상수로 분리한 뒤 `build.gradle.kts`에서 참조한다.
   - 자세한 규칙은 `references/build-configuration.md`를 확인한다.

6. 컴파일만 보지 말고 동작을 검증한다.
   - 대상 프로젝트에서 제공하는 관련 Gradle check/test를 실행한다.
   - 신규 API는 success, not found, validation failure, invalid path/query/body input, trace ID, read/write datasource routing이 있는 경우 persistence routing까지 확인한다.

## 레퍼런스 선택

작업에 필요한 파일만 읽는다.

- `references/architecture.md`: 패키지 트리, 계층 책임, 의존성 규칙, 리뷰 체크리스트.
- `references/domain-workflow.md`: 도메인 추가/수정 단계별 절차.
- `references/common-package.md`: `common` 하위 패키지별 역할과 금지 사항.
- `references/webflux-validation-error-i18n.md`: WebFlux coroutine handler, request binding, validation, i18n, message resolver, error response, trace ID.
- `references/persistence-jooq-transaction.md`: jOOQ generation, read/write datasource routing, transaction port/adapter, blocking JDBC 처리.
- `references/build-configuration.md`: Gradle Kotlin DSL 의존성 범주, buildSrc 버전 관리, configuration processor, 정적 분석.

## 구조 점검

패키지 구조를 참고용으로 점검하려면 실행한다.

```bash
python3 <skill-dir>/scripts/check_structure.py <project-root> --base-package com.example.yourapp
```

이 스크립트는 누락된 package family와 common module을 보고한다. partial project, multi-module project, MVC-only project, non-jOOQ project에서는 참고 신호로만 사용하고 hard failure로 보지 않는다.
