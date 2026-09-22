# 코딩 · 응답 · 예외 규약

정본 우선순위: **① 주변 코드 → ② `docs/ai/04_coding_standards/backend-core-coding-standards.md` →
③ 이 문서**. 루트 `313DEVGRP-Rule.txt` 는 실제 코드와 상충하는 레거시 문서이므로 따르지 않는다.

---

## 1. 언어 · 버전

| 항목 | 값 |
|---|---|
| Java | **11** (`sourceCompatibility`/`targetCompatibility = 11`) |
| Spring Boot | **2.6.15** |
| Spring Cloud | **2021.0.9** |
| Hibernate | 5.6.15.Final |
| Gradle | 6.9.1 |
| 패키지 | `javax.*` (**`jakarta.*` 금지**) |

금지: record, sealed, text block 남용, `switch` 표현식, `List.of` 외 Java 17+ API,
Boot 3 전용 API(`jakarta.servlet`, `@ConfigurationProperties` 생성자 바인딩 신문법 등).

---

## 2. 계층 · 네이밍

```
com.arms.api.<domain>/
  controller/  <Domain>Controller.java
  service/     <Domain>.java 또는 <Domain>Service.java  (인터페이스)
               <Domain>Impl.java 또는 <Domain>ServiceImpl.java
  model/       entity/<Domain>Entity.java   dto/<Domain>DTO.java   vo/<Domain>VO.java
```

- 인터페이스 이름은 도메인에 따라 **두 관례가 공존**한다:
  트리 도메인은 접미사 없음(`ReqAdd` / `ReqAddImpl`, `PdService` / `PdServiceImpl`),
  비트리 도메인은 `Service` 접미사(`BlogService` / `BlogServiceImpl`).
  **새 파일은 같은 패키지의 기존 관례를 따른다.**
- `@Service("<빈이름>")` 으로 **이름 지정 빈**을 만들고 컨트롤러는 `@Qualifier("<빈이름>")` 로 주입한다.
  `TreeServiceImpl` 자신이 `@Service("treeService")` 라서 타입 기준 주입이 모호해지기 때문이다.
- 클래스 PascalCase / 메서드·변수 camelCase / 상수 UPPER_SNAKE.
- **패키지는 소문자, 도메인 스네이크 허용**: `detail_dashboard`, `reqstate_category`, `product_service`.
- DB: 테이블 `T_ARMS_*`, 컬럼 `c_` + snake_case. **엔티티 필드명 = 컬럼명**(property access 때문).
- **한글 식별자가 기존 관례인 곳이 있다**: `EngineService`(`이슈_생성하기`), `ReqAdd`(`요구사항_생성처리`),
  `model/요구사항_담당자.java`, `model/vo/버전표현VO.java`. 해당 도메인에서는 유지한다.
  새로 만드는 공용/설정 코드에는 쓰지 않는다.

### 의존성 주입

```java
@RequiredArgsConstructor          // 신규 권장
public class XxxServiceImpl {
    private final YyyService yyyService;
}
```
기존 도메인의 `@Autowired @Qualifier("reqAdd") private ReqAdd reqAdd;` 필드 주입은
**그대로 둔다**(요청 없이 리팩토링하지 않는다).

---

## 3. 컨트롤러

- 애노테이션: `@RestController`(또는 `@Controller` + `@ResponseBody`) + `@RequestMapping`.
  `@Slf4j` 를 함께 붙인다.
- **경로 prefix (실제 코드 기준)**:

  | prefix | 개수 | 예 |
  |---|---|---|
  | `/arms/**` | 78 | `/arms/reqAdd`, `/arms/pdService`, `/arms/export/reports` |
  | `/admin/arms/**` | 6 | `/admin/arms/analysis/cost`, `/admin/arms/salaries` |
  | `/anonymous/**` | 4 | `/anonymous/arms/blog`, `/anonymous/cover/newsletter` |
  | 기타 | 2 | `/kafka`, `/html/mail` |

  **`/auth-user`, `/auth-manager`, `/auth-admin`, `/auth-sche` 는 이 저장소에 없다.**
  게이트웨이(Middle-Proxy)가 `/auth-user/api/arms/...` 를 받아 `/arms/...` 로 전달한다.
  새 컨트롤러에 `/auth-*` 를 직접 쓰지 않는다.
- 엔드포인트 접미사는 도메인 관례를 따른다 — 트리/레거시는 `.do`, 신규 REST 는 하이픈 경로
  (`/req-property-list`, `/project-status`).
- HTTP 메서드: 조회 GET · 생성 POST · 수정 PUT · 삭제 DELETE.
- 트리 도메인은 `@PostConstruct initialize()` 에서 `setTreeService` · `setTreeEntity` 필수.

---

## 4. 응답 형태 — 두 가지, 섞지 않는다

### (A) `jsonView` — 트리 공통/레거시 `.do`

```java
ModelAndView mv = new ModelAndView("jsonView");
mv.addObject("result", payload);
return mv;
```

`context-common.xml` 의 `jsonView` = `MappingJackson2JsonView`
(`modelKey=result`, `extractValueFromSingleKeyModel=true`, `prettyPrint=true`,
`contentType=application/json;charset=UTF-8`, `objectMapper` 주입).

→ **응답 본문은 `payload` 그 자체**다. `{"result": …}` 로 감싸지지 않는다.
단, `addObject("result", Map.of("paginationInfo",…, "result",…))` 처럼 맵을 넣으면 그 맵이 본문이 된다.

### (B) `CommonResponse.ApiResult<T>` — 신규 REST

```java
return ResponseEntity.ok(CommonResponse.success(vo));
// {"success": true, "response": {...}, "error": null}
```

에러 형태: `{"success": false, "response": null, "error": {"message","errorCode","status"}}`

> 프론트(`Frontend-Web`)가 `data.response` 유무로 구/신형을 구분한다.
> **기존 `.do` 엔드포인트의 응답 형태를 바꾸면 화면이 깨진다.**

`ResponseEntity<Entity>` 를 그대로 반환하는 기존 패턴도 있으나, **신규는 VO/DTO** 로 응답한다
(지연로딩·순환참조 직렬화 사고 방지).

---

## 5. 예외 처리

전역: `ErrorControllerAdvice`(`@ControllerAdvice`, `treeframework/errors/response/`)

| 예외 | HTTP | 부가 동작 |
|---|---|---|
| `BaseException` (및 하위) | **400** | **Slack `backend` 채널로 알림** + `log.warn`/`log.error` |
| `MethodArgumentNotValidException` | 400 | 첫 필드 에러 메시지 조합 |
| `BindException` | 400 | 첫 에러 메시지 |
| `ClientAbortException` | **200** | 모니터링 skip |
| 그 외 `Exception` | 500 | `log.error` + 최심 원인 로깅 |

리포트 전용: `ReportExceptionHandler`
(`@RestControllerAdvice(basePackages = "com.arms.api.report.export_service")`).

`ErrorCode` enum: `COMMON_SYSTEM_ERROR` · `COMMON_INVALID_PARAMETER` · `COMMON_ENTITY_NOT_FOUND` ·
`COMMON_ILLEGAL_STATUS` · `COMMON_ID_NOT_FOUND` · `COMMON_DUPLICATE_FOUND` · `COMMON_TREE_DAO_ERROR`.

규칙:
- **컨트롤러에서 try/catch 로 500 응답을 직접 만들지 않는다.** 전역 advice 에 맡긴다.
- 비즈니스 오류는 `BaseException` 계열(`EntityNotFoundException`, `IDNotFoundException`,
  `DuplicateFoundException`, `InvalidParamException`, `ServiceProcessException`)을 던진다.
  단 **Slack 알림이 나간다**는 점을 감안한다 — 사용자 입력 오류를 `BaseException` 으로 남발하지 않는다.
- 컨트롤러 시그니처의 `throws Exception` 은 기존 관례다. 유지해도 되지만 신규는 구체 예외를 권장.

---

## 6. 로깅

```java
@Slf4j
...
log.info("[ ReqAddController :: getMonitor ] :: 조회 시작 => {}", changeReqTableName);
```

- 형식: `[ 클래스 :: 메서드 ] :: 설명 => {}`
- **`System.out.println` 금지.** 공통 프레임워크(`TreeServiceImpl.stretchLeft/Right`, `removeNode`)에
  남아 있는 것은 기존 코드다 — 따라하지 않고, 요청 없이 고치지도 않는다.
- **크리덴셜·토큰·개인정보를 로그에 남기지 않는다.**
- 로깅 설정: `logback/logback-{dev,stg,live,mklee}.xml` + `console-appender.xml`.
  SQL 로깅은 `log4jdbc`(`log4jdbc.log4j2.properties`)로 제어한다.

---

## 7. Swagger

`Swagger2Config` — `@EnableSwagger2`(springfox 3.0.0), `basePackage("com")`, 모든 경로.
`TreeBaseEntity` · `PaginationInfo` · `Projection` · `List<Order>` 는
`directModelSubstitute`/`alternateTypeRules` 로 **Enum 으로 치환**해 문서에서 감춘다.

엔티티에 필드를 추가할 때, 내부 처리용이면 `@ApiModelProperty(hidden = true)` 를 붙인다.
공개 API 필드는 `@ApiOperation` / `@ApiModelProperty(value = "설명")` 으로 설명을 남긴다.

---

## 8. 설정 · 시크릿

- `application.yml` 에는 앱 이름·로깅 설정만 있다. **실제 값은 전부 Config Server(Global-Config)** 에서 온다.
  (`arms.engine.url`, `arms.ai.url`, `arms.middle-proxy.url`, `database.*`, `cors.allowed-origins`,
  `spring.kafka.*`, `spring.flyway.*`, `spring.datasource.hikari.*`)
- 주입은 `@Value` / `@ConfigurationProperties`. 런타임 갱신이 필요하면 `@RefreshScope`
  (`WebConfig`, `KafkaConfig` 가 그렇게 돼 있다).
- **새 시크릿을 소스·yml 에 평문으로 넣지 않는다.**
  기존에 이미 노출된 것들(`build.gradle` 의 SonarQube 계정, `settings.xml` 의 Nexus 계정)은
  **건드리지 말고**, 새로 추가만 하지 않는다. 발견 사실은 보고한다.

---

## 9. 커밋

브랜치 `dev`. YouTrack 연동 형식:

```
feat : [ARMS-1160] #comment 담당자별 진행율 로직 추가
fix : [ARMS-1160] #comment 월별, 주별 진척율 기간 오류 수정
refactor : [ARMS-1134] #comment ReqAddController::moveNodeFromKafka 메소드 리팩토링 26.08.10 #close #time 1h +review SR @sevoon0909
```

- 타입: `feat` / `fix` / `refactor` (콜론 앞뒤 공백은 커밋마다 제각각이다 — 최근 커밋을 따른다)
- **commit·push 는 사용자가 한다.** 초안만 제시한다.
