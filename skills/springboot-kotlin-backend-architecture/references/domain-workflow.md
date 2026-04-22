# 도메인 작업 흐름 레퍼런스

신규 도메인이나 큰 도메인 기능을 추가할 때 이 체크리스트를 따른다.

## 1. Domain

도메인 모델은 아래에 만든다.

```text
domain/{domain}/model/
├── {Entity}.kt
└── {Status}.kt
```

지침:

- 상태와 invariant는 plain Kotlin으로 모델링한다.
- enum을 안정적인 database value로 저장해야 하면 `GenericEnum`을 구현한다.
- enum을 i18n label이나 display order와 함께 노출해야 하면 `DisplayEnum`을 구현한다.
- request DTO, response DTO, jOOQ record, WebFlux type에 의존하지 않는다.

## 2. Application Input Port

Use case와 command/query model을 만든다.

```text
application/port/input/{domain}/
├── {Domain}UseCase.kt
└── model/
    ├── Create{Entity}Command.kt
    ├── Update{Entity}Command.kt
    └── {Entity}SearchQuery.kt
```

지침:

- Application 입력은 command/query model로 표현한다.
- 대상 프로젝트가 application model validation을 의도적으로 쓰는 경우가 아니라면 request DTO validation annotation은 `adapter/input/web/.../protocol`에 둔다.
- Use case는 HTTP response DTO가 아니라 domain model 또는 application result model을 반환한다.

## 3. Application Output Port

Outbound port interface를 만든다.

```text
application/port/output/{domain}/
└── {Domain}Port.kt
```

일반적인 port method:

- `findById(id): Entity?`
- `findByFilter(query fields): List<Entity>`
- `insert(...)`
- `update(...)`
- `delete(id): Boolean`

Port는 기술 중립적으로 유지한다. `DSLContext`, generated table record, SQL string, WebClient response, database-specific exception을 port signature에 노출하지 않는다.

## 4. Application Service

아래 파일을 만든다.

```text
application/service/{Domain}Service.kt
```

지침:

- 대상 프로젝트가 component scanning을 사용하면 Spring service로 등록한다.
- Input use case를 구현한다.
- Output port와 `TransactionalPort`에 의존한다.
- Read operation은 `executeReadOnly`, mutation은 `execute`로 감싼다.
- 필요한 데이터가 없거나 상태 전이가 유효하지 않으면 domain-specific exception을 던진다.

## 5. Inbound Web Adapter

아래 파일을 만든다.

```text
adapter/input/web/{domain}/
├── {Domain}Router.kt
├── {Domain}Handler.kt
└── protocol/
    ├── Create{Entity}Request.kt
    ├── Update{Entity}Request.kt
    ├── {Entity}SearchRequest.kt
    └── {Entity}Response.kt
```

지침:

- WebFlux coroutine 프로젝트에서는 `coRouter`와 `suspend` handler를 사용한다.
- Handler는 얇게 유지한다: request parse, validation, use case 호출, response 반환.
- Request DTO는 DTO method나 mapper function으로 command/query model로 변환한다.
- Domain/application 결과는 adapter boundary에서 response DTO로 변환한다.
- Query binding, enum path variable, required header, body validation은 common request helper를 사용한다.

## 6. Outbound Persistence Adapter

아래 파일을 만든다.

```text
adapter/output/persistence/jooq/{domain}/
└── {Domain}PersistenceAdapter.kt
```

지침:

- Output port를 구현한다.
- Generated jOOQ table reference는 adapter 안에서만 사용한다.
- Record를 domain model로 변환하는 private mapper를 둔다.
- `GenericEnum.value`를 database column에 저장한다.
- Persisted enum value는 `requireByValue`로 변환한다. 잘못 저장된 DB value는 client validation 실패가 아니라 server/data-integrity error로 취급한다.

## 7. Error Code And Message

아래 파일을 만들거나 확장한다.

```text
common/errors/{Domain}ErrorCode.kt
src/main/resources/errors/error.properties
```

패턴:

```kotlin
enum class {Domain}ErrorCode(
    override val code: String,
    override val label: String,
) : ErrorCode {
    {ENTITY}_NOT_FOUND("E{PREFIX}001", "{domain}.{Domain}ErrorCode.{ENTITY}_NOT_FOUND"),
}
```

메시지를 추가한다.

```properties
{domain}.{Domain}ErrorCode.{ENTITY}_NOT_FOUND={Entity}를 찾을 수 없습니다. ID: {0}
```

도메인마다 안정적인 code prefix를 사용한다. Client-facing message는 resource bundle에 둔다.

## 8. Schema And jOOQ

Persistence가 바뀌면 다음 순서로 진행한다.

1. 대상 프로젝트가 사용하는 DDL 또는 migration source를 수정한다.
2. Generated jOOQ table을 사용하는 프로젝트라면 jOOQ source를 재생성한다.
3. Persistence adapter가 generated type을 사용하도록 수정한다.
4. Compile과 관련 integration test를 실행한다.

## 검증 체크리스트

신규 API 도메인은 다음을 확인한다.

- Create/read/update/delete 또는 해당 business flow.
- Query parameter가 있다면 search/filter behavior.
- Not found exception과 error code.
- Validation failure와 field errors.
- Invalid path parameter와 invalid enum path parameter.
- Query parameter binding failure.
- 필요한 경우 empty/malformed body.
- 필요한 경우 required header failure.
- Trace ID infrastructure가 있으면 response header/body behavior.
- Read/write split이 있으면 datasource routing.
- jOOQ mapping에서 enum `value` 저장/변환.
