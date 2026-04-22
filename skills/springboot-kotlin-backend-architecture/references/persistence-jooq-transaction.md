# Persistence, jOOQ, Transaction 레퍼런스

## jOOQ Code Generation

jOOQ를 사용할 때는 프로젝트의 schema source에서 Kotlin source를 생성한다. Skeleton은 DDL 기반 생성을 사용한다.

```kotlin
jooq {
    configuration {
        generator {
            name = "org.jooq.codegen.KotlinGenerator"
            database {
                name = "org.jooq.meta.extensions.ddl.DDLDatabase"
                properties {
                    property {
                        key = "scripts"
                        value = "src/main/resources/db/schema.sql"
                    }
                }
            }
            target {
                packageName = "{basePackage}.jooq.generated"
                directory = jooqGeneratedDir.get().asFile.absolutePath
            }
        }
    }
}
```

Generated source를 등록한다.

```kotlin
kotlin {
    sourceSets.named("main") {
        kotlin.srcDir(jooqGeneratedDir)
    }
}

tasks.named("compileKotlin") {
    dependsOn(tasks.named("jooqCodegen"))
}
```

Generator version, package name, schema source는 대상 프로젝트에 맞춘다.

## Persistence Adapter 규칙

Persistence adapter는 아래에 둔다.

```text
adapter/output/persistence/jooq/{domain}/
```

규칙:

- `application.port.output.{domain}.{Domain}Port`를 구현한다.
- `DSLContext`를 주입받는다.
- Generated jOOQ table reference는 adapter 내부에서만 사용한다.
- jOOQ record가 아니라 domain model을 반환한다.
- `toEntity(record)` 같은 private mapper function을 사용한다.
- SQL condition은 adapter 안에서 읽기 쉽게 유지한다.
- Database enum value는 adapter boundary에서 domain enum으로 변환한다.

Enum persistence:

- `GenericEnum.value`를 database column에 저장한다.
- Query에는 `enum.value`를 사용한다.
- DB value는 `requireByValue<EnumType>(value)`로 변환한다.
- 잘못 저장된 enum value는 server/data-integrity error로 취급한다.

## Read/Write Datasource Routing

Read/write traffic을 분리하는 프로젝트에서는 다음 구성을 사용한다.

- `@ConfigurationProperties`로 `writeHikariConfig`, `readHikariConfig`를 bind한다.
- `writeDataSource`, `readDataSource`를 만든다.
- `LazyConnectionDataSourceProxy(writeDataSource)`를 사용해 primary `dataSource`를 노출한다.
- Proxy에 read-only datasource를 설정한다.
- 프로젝트 요구사항에 맞는 transaction isolation을 명시한다.
- `isReadOnly = false`인 `writeTransactionTemplate`을 정의한다.
- `isReadOnly = true`인 `readTransactionTemplate`을 정의한다.

레퍼런스 구조:

```kotlin
@Bean("dataSource")
@Primary
fun dataSource(writeDataSource: DataSource, readDataSource: DataSource): DataSource =
    LazyConnectionDataSourceProxy(writeDataSource).apply {
        setReadOnlyDataSource(readDataSource)
        setDefaultTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED)
    }
```

## Transaction Port

Transaction execution은 output port로 노출한다.

```kotlin
interface TransactionalPort {
    suspend fun <T> execute(block: () -> T): T
    suspend fun <T> executeReadOnly(block: () -> T): T
}
```

Application service는 `TransactionTemplate`이 아니라 `TransactionalPort`에 의존한다.

## WebFlux에서 Blocking JDBC 처리

JDBC 기반 jOOQ는 blocking이다. WebFlux application에서는 다음을 지킨다.

- Blocking jOOQ/JDBC 호출을 event-loop thread에서 실행하지 않는다.
- 전체 transaction callback을 dedicated coroutine dispatcher에서 실행한다.
- 가능하고 적절한 runtime이면 blocking JDBC 작업에 Java virtual thread를 사용한다.
- Spring JDBC transaction state가 유지되도록 전체 callback을 같은 execution context에서 처리한다.

레퍼런스 adapter 형태:

```kotlin
private suspend fun <T> runInTransaction(
    transactionTemplate: TransactionTemplate,
    block: () -> T,
): T = withContext(databaseCoroutineDispatcher) {
    var result: Any? = UninitializedResult
    transactionTemplate.execute {
        result = block()
    }
    result as T
}
```

대상 runtime에서 virtual thread를 사용할 수 없다면 bounded dispatcher 또는 프로젝트의 blocking I/O executor를 사용한다.

## 검증

Persistence 변경 시 다음을 확인한다.

- jOOQ code generation이 성공한다.
- Generated source package가 import와 일치한다.
- Application service가 read에는 `executeReadOnly`, mutation에는 `execute`를 사용한다.
- Read endpoint가 read/write split 환경에서 read datasource를 사용한다.
- Mutating endpoint가 write datasource를 사용한다.
- Transaction이 의도한 dispatcher에서 실행된다.
- Enum value 저장/변환이 테스트로 검증된다.
