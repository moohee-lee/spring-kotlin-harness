# 아키텍처 레퍼런스

## 기본 구조

대상 프로젝트의 base package 아래에 Hexagonal Architecture + DDD 구조를 둔다.

```text
{basePackage}/
├── adapter/
│   ├── input/web/{domain}/
│   │   ├── {Domain}Router.kt
│   │   ├── {Domain}Handler.kt
│   │   └── protocol/
│   │       ├── Create{Entity}Request.kt
│   │       ├── Update{Entity}Request.kt
│   │       └── {Entity}Response.kt
│   └── output/
│       ├── persistence/config/
│       ├── persistence/jooq/{domain}/
│       │   └── {Domain}PersistenceAdapter.kt
│       └── transaction/
│           └── TransactionalExecutorAdapter.kt
├── application/
│   ├── port/
│   │   ├── input/{domain}/
│   │   │   ├── {Domain}UseCase.kt
│   │   │   └── model/
│   │   │       ├── Create{Entity}Command.kt
│   │   │       ├── Update{Entity}Command.kt
│   │   │       └── {Entity}SearchQuery.kt
│   │   └── output/{domain}/
│   │       └── {Domain}Port.kt
│   └── service/
│       └── {Domain}Service.kt
├── domain/{domain}/model/
│   ├── {Entity}.kt
│   └── {Status}.kt
└── common/
```

대상 프로젝트의 실제 base package를 사용한다. 실제 base package가 아닌 이상 `com.example.skeleton`을 그대로 남기지 않는다.

## 계층별 책임

- `domain`: 핵심 비즈니스 모델, domain enum, value object, invariant를 둔다. transport, persistence, Spring configuration, generated jOOQ record와 독립적으로 유지한다.
- `application`: use case, command/query model, service, port를 둔다. Service는 domain behavior와 port를 조합하며 concrete adapter class를 알지 않는다.
- `adapter/input`: WebFlux router/handler 같은 inbound protocol을 둔다. HTTP request를 command/query로 변환하고 application/domain 결과를 response DTO로 변환한다.
- `adapter/output`: persistence, external client, messaging, transaction execution 같은 outbound integration을 둔다. output port 구현체가 여기에 위치한다.
- `common`: 여러 도메인에서 재사용되는 cross-cutting infrastructure를 둔다.

## 의존성 규칙

허용 방향:

```text
adapter -> application -> domain
adapter -> common
application -> common
domain -> common only for stable, domain-safe primitives if necessary
```

피해야 할 구조:

- Handler가 persistence adapter를 직접 주입받는 구조.
- Router, handler, request DTO, persistence adapter에 business rule을 넣는 구조.
- Use case가 request/response DTO를 반환하는 구조.
- Domain model이 jOOQ record, DB row, HTTP DTO를 받는 구조.
- `domain`에서 WebClient, DSLContext, repository, external system을 호출하는 구조.
- global exception handler, validator, message converter를 도메인별로 복제하는 구조.

## 리뷰 체크리스트

- Inbound route는 adapter가 아니라 use case interface를 호출한다.
- Service는 concrete persistence class가 아니라 output port와 transaction port에 의존한다.
- Persistence adapter는 output port를 구현한다.
- Domain entity는 WebFlux, jOOQ, JDBC, Spring configuration, HTTP DTO를 import하지 않는다.
- `common`에는 재사용 가능한 infrastructure만 있고 domain-specific workflow는 없다.
- 새 business exception에 대한 error code와 message가 등록되어 있다.
- 테스트가 DTO mapping만이 아니라 계층 integration point를 검증한다.
