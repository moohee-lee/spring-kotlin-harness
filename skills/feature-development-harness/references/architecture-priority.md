# Architecture Priority

For Spring Boot Kotlin backend development, always load `springboot-kotlin-backend-architecture` before implementation or review.

The architecture skill owns these decisions:

- `adapter`, `application`, `domain`, `common` package boundaries.
- Dependency direction.
- Use case, command/query model, output port, service, handler, and persistence adapter placement.
- Error code, validation, i18n, WebFlux coroutine, jOOQ, transaction, and build configuration conventions.

Conflict rule:

```text
workflow engine suggestion < springboot-kotlin-backend-architecture rule
```

Examples of corrections to preserve:

- Handler must call use case interfaces, not persistence adapters.
- Service must depend on output ports, not concrete adapter classes.
- Domain model must not import Spring, WebFlux, jOOQ, JDBC, request DTO, or response DTO types.
- Reusable infrastructure belongs in `common`; domain-specific workflow does not.
