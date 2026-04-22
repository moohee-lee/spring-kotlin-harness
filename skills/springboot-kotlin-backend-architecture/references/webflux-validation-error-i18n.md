# WebFlux, Validation, Error, i18n 레퍼런스

## WebFlux Coroutine 스타일

WebFlux 프로젝트에서는 functional routing과 coroutine handler를 우선 사용한다.

```kotlin
@Bean
fun domainRoutes(): RouterFunction<ServerResponse> = coRouter {
    (accept(MediaType.APPLICATION_JSON) and version(API_VERSION_V1) and "/domain/{version}").nest {
        GET("items", handler::searchItems)
        GET("items/{id}", handler::getItem)
        POST("items", handler::createItem)
        PUT("items/{id}", handler::updateItem)
        DELETE("items/{id}", handler::deleteItem)
    }
}
```

Handler 규칙:

- Handler function은 `suspend`로 만든다.
- Path variable은 명시적으로 parse하고, 유효하지 않으면 request validation exception을 던진다.
- Query field가 여러 개면 query parameter를 request DTO로 bind한다.
- Request body는 command model로 변환하기 전에 validate한다.
- Response DTO는 adapter layer에서 반환한다.

일반적인 helper 사용:

```kotlin
val query = request.bindQueryParams<SearchRequest>()
validator.validateOrThrow(query)

val status = request.enumPathVariable<Status>("status")
val modifiedBy = request.headerOrThrow("X-Modified-By")
val body = request.awaitBodyValidated<CreateRequest>(validator)
```

대상 Spring Boot 버전이 `ApiVersionConfigurer` 또는 `RequestPredicates.version`을 지원하지 않으면 route shape는 유지하되 explicit path segment나 프로젝트의 기존 versioning 전략을 사용한다.

## WebFlux Configuration

WebFlux infrastructure는 한 번만 설정한다.

- `DefaultMessageCodesResolver.Format.POSTFIX_ERROR_CODE`를 사용하는 `MessageCodesResolver`.
- Application `MessageSource`를 사용하는 `LocalValidatorFactoryBean`.
- Application validator를 반환하는 `getValidator()`.
- Shared resolver를 반환하는 `getMessageCodesResolver()`.
- 대상 Spring version에서 지원하면 API versioning.
- Common constant를 사용한 HTTP codec max in-memory size.

Per-domain validation rule은 global WebFlux config가 아니라 request DTO field 또는 domain/application rule에 둔다.

## i18n Message Resource

Resource bundle은 용도별로 나눈다.

```yaml
spring:
  messages:
    basename: messages/message,validations/validation,enums/enum,errors/error
    fallback-to-system-locale: false
  web:
    locale: ko_KR
```

권장 파일:

```text
src/main/resources/errors/error.properties
src/main/resources/enums/enum.properties
src/main/resources/validations/validation.properties
src/main/resources/messages/message.properties
```

사용 기준:

- Error message는 `errors/error.properties`에 둔다.
- Enum display label은 `enums/enum.properties`에 둔다.
- Bean Validation message는 `validations/validation.properties`에 둔다.
- 일반 application message는 `messages/message.properties`에 둔다.

Application code에서 code, args, locale 기반 message lookup이 필요하면 `MessageConverter` wrapper를 사용한다. Error code도 같은 message source를 통해 message를 제공한다.

## Error Code 패턴

공통 contract를 정의한다.

```kotlin
interface ErrorCode {
    val code: String
    val label: String
}
```

지침:

- `code`: `EKCP010` 같은 안정적인 client-facing machine code.
- `label`: `common.CommonErrorCode.VALIDATION_FAIL` 같은 message resource key.
- Common HTTP/platform error는 `CommonErrorCode`에 둔다.
- Domain error는 안정적인 domain error-code enum에 둔다.
- 새 error-code label은 모두 `errors/error.properties`에 추가한다.

## Exception 패턴

Status, error code, message args, cause를 담는 base exception을 사용한다.

```kotlin
abstract class DefaultException(
    val status: HttpStatus,
    val errorCode: ErrorCode,
    val messageArguments: Array<Any> = emptyArray(),
    cause: Throwable? = null,
) : RuntimeException(errorCode.getMessage(messageArguments), cause)
```

Client input failure에는 request validation exception을 사용한다. 포함할 정보:

- HTTP status, 보통 `400`.
- Error code.
- `ApiFieldError` list.
- Source: `BODY`, `QUERY`, `PATH`, `HEADER`.
- Field name.
- Client-facing message.

Not found, conflict, forbidden state transition 같은 business failure에는 domain exception을 사용한다.

## Error Response Shape

일관된 JSON을 반환한다.

```json
{
  "status": 400,
  "code": "EKCP010",
  "message": "유효성 검사에 실패했습니다.",
  "path": "/domain/1.0/items",
  "traceId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "errors": [
    {
      "source": "BODY",
      "field": "name",
      "message": "must not be blank"
    }
  ]
}
```

`errors`는 optional이며 비어 있으면 응답에서 제외한다.

## Global Error Mapping

Exception-to-response mapping은 WebFlux error pipeline에서 중앙화한다.

- `DefaultException`: exception status, error code, message args, validation field errors를 사용한다.
- `WebExchangeBindException`: Spring binding failure를 `VALIDATION_FAIL`과 body field error로 매핑한다.
- `ConstraintViolationException`: Bean Validation failure를 `VALIDATION_FAIL`로 매핑한다.
- `ServerWebInputException`: malformed JSON, invalid format, mismatched input을 bad request code로 매핑한다.
- `InvalidMediaTypeException`: unsupported media type으로 매핑한다.
- `DataBufferLimitException`: payload too large로 매핑한다.
- `ResponseStatusException`: framework status를 common error code로 매핑한다.
- Unknown exception: generic client-facing message를 가진 internal server error로 매핑한다.

기본적으로 stack trace나 internal exception message를 client에 노출하지 않는다.

## Trace ID

WebFilter에서 trace ID를 다음 우선순위로 결정한다.

1. `X-Trace-Id`
2. W3C `traceparent`
3. Zipkin `X-B3-TraceId`
4. dash 없는 generated UUID

Trace ID를 exchange attributes에 저장하고, `X-Trace-Id` response header로 반환하며, error response에도 포함한다. 로그에서 trace ID를 볼 수 있도록 Reactor/coroutine MDC propagation을 설정한다.
