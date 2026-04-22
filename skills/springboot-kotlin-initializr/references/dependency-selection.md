# Dependency Selection

의존성 선택은 `SPRING_INITIALIZR_DEPENDENCIES.md` 체크박스 파일로 진행한다.

## 파일 형식

```markdown
# Spring Initializr Dependencies

<!-- spring-initializr: boot_request=default boot_effective=4.0.5 java_request=default java_effective=17 kotlin_request=default group=com.example artifact=demo package=com.example.demo -->

## 생성 값

- Spring Boot: default -> 4.0.5
- Java: default -> 17
- Kotlin: default
- Group: com.example
- Artifact: demo
- Package: com.example.demo

## 사용 방법

- 설치할 dependency의 `[ ]`를 `[x]`로 바꾸세요.
- backtick 안의 dependency id는 수정하지 마세요.
- 수정을 마치면 Codex에게 계속 진행하라고 알려주세요.

## Web

- [ ] `webflux` - Spring Reactive Web: Build reactive web applications with Spring WebFlux and Netty.
- [ ] `spring-webclient` - Reactive HTTP Client: Spring Boot integration for WebClient.
```

## 생성 규칙

- Initializr metadata의 category 순서를 보존한다.
- 선택한 Boot version의 `/dependencies?bootVersion=...` resolved map에 있는 dependency만 표시한다.
- 각 항목에는 dependency id, name, description, versionRange가 있으면 표시한다.
- dependency id는 backtick으로 감싼다.

## 파싱 규칙

선택으로 인정하는 형식:

```markdown
- [x] `webflux` - Spring Reactive Web: ...
- [X] `validation` - Validation: ...
```

선택으로 인정하지 않는 형식:

```markdown
- [v] `webflux`
- [x] webflux
```

체크된 dependency id가 파일에 표시된 dependency id 목록에 없으면 중단한다.

## 자동 추가 의존성

Skeleton overlay는 다음 Initializr dependency를 필요에 따라 자동 추가한다.

- `webflux`
- `validation`
- `configuration-processor`
- `jooq`
- `h2`
- `actuator`
- `spring-webclient` if compatible with selected Boot version

사용자가 선택하지 않아도 overlay 단계에서 required set에 추가한다. 단, 선택한 Boot version에서 Initializr가 제공하지 않는 dependency는 추가하지 않고 보고한다.
