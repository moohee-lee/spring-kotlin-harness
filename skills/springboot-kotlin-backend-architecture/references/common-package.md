# Common Package 레퍼런스

`common`은 안정적인 cross-cutting infrastructure를 위한 위치다. Domain-specific rule을 모아두는 공간으로 쓰지 않는다.

## 권장 구조

```text
common/
├── CommonObjectMapper.kt
├── config/
├── constant/
├── enums/
├── errors/
├── exception/
├── extensions/
└── utils/
```

## `common.config`

Infrastructure configuration을 둔다.

- `CommonConfiguration`: primary ObjectMapper 같은 shared bean.
- `WebFluxConfiguration`: validator, message code resolver, API versioning, max in-memory size.
- `GlobalExceptionHandler`: 모든 실패를 unified response renderer로 보내는 WebFlux error handler.
- `GlobalErrorAttributes`: framework/custom exception을 API error response로 변환.
- `TraceIdWebFilter`: trace ID 추출/생성, response header 전파.
- `TraceLoggingConfiguration`: Reactor/coroutine MDC context propagation.
- `WebClientConfiguration`: shared WebClient builder 설정, codec limit, timeout.

Domain-specific route, port, service, persistence setting은 여기에 두지 않는다.

## `common.constant`

전역 상수만 둔다.

- `MAX_BUFFER_SIZE`
- `API_VERSION_V1` 같은 API version constant
- `DEFAULT_LOCALE`
- 여러 도메인에서 사용하는 안정적인 header name

한 도메인에서만 쓰는 값은 해당 도메인에 둔다.

## `common.enums`

Enum contract와 shared enum infrastructure를 둔다.

- `GenericEnum`: database storage value contract.
- `DisplayEnum`: presentation label, ordering, displayable contract.
- `DatePatternEnum`: shared date/time formatting pattern.

Domain-specific enum은 정말 여러 bounded context에서 공유되는 경우가 아니라면 `domain/{domain}/model`에 둔다.

## `common.errors`

Error code contract와 response DTO를 둔다.

- `ErrorCode`: `code`, `label`, message lookup을 제공한다.
- `CommonErrorCode`: common HTTP/platform error code.
- `{Domain}ErrorCode`: 프로젝트가 error code enum을 중앙화한다면 domain-specific error code enum.
- `ApiErrorResponse`: `status`, `code`, `message`, `path`, `traceId`, optional `errors`를 포함하는 response shape.
- `ApiFieldError`: field-level validation error.
- `ErrorSource`: `BODY`, `QUERY`, `PATH`, `HEADER`.
- Default field name이나 fallback message 같은 error constant.

Public client가 의존하는 error code는 한 번 공개한 뒤 안정적으로 유지한다.

## `common.exception`

Exception hierarchy를 둔다.

- `DefaultException`: `HttpStatus`, `ErrorCode`, message arguments, cause를 가진 base runtime exception.
- 공통 auth/permission/token exception.
- `ApiFieldError`를 담는 request validation exception.
- 프로젝트가 exception class를 중앙화한다면 domain exception.

규칙:

- Business exception은 `ErrorCode`를 가진다.
- Request validation exception은 field source와 field name을 식별한다.
- Domain not-found/conflict/state exception은 domain error code로 매핑한다.
- Domain error code가 필요한 상황에서 raw framework exception을 application service에서 그대로 던지지 않는다.

## `common.extensions`

반복되는 Kotlin helper를 둔다.

- Database `value` 또는 display `label` 기반 enum lookup.
- Enum path variable, query binding, required header, body validation을 위한 `ServerRequest` helper.
- `validateOrThrow` 같은 Validator helper.
- Jackson serialization/deserialization helper.
- Coroutine parallel execution helper.
- Collection, date/time helper.

Helper는 작고 넓게 재사용 가능해야 한다. Domain-specific helper는 해당 domain package로 옮긴다.

## `common.utils`

작은 infrastructure utility를 둔다.

- `MessageConverter`: Spring `MessageSource`에서 code, args, locale 기반으로 message를 조회하고 fallback behavior를 제공한다.

Spring이 의도적으로 초기화하고 테스트로 보장하는 경우가 아니라면 global mutable utility state는 피한다.

## `common`에 두지 말 것

- Business workflow.
- Domain-specific query construction.
- Domain policy 또는 validation rule.
- 한 API에만 쓰는 request/response DTO.
- Persistence adapter.
- External client adapter.
- Generated jOOQ code.
- 한 도메인 전용 test fixture.
