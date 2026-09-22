# 외부 연동 — Feign · Kafka · DWR · Slack · 메일 · 스케줄러

---

## 1. Feign 클라이언트 전체 목록

전부 `com/arms/api/util/communicate/` 아래에 있고 `OpenFeignConfig` 가
`@EnableFeignClients({"com.arms.api.util.communicate"})` 로 스캔한다.

| 인터페이스 | `@FeignClient` | URL 프로퍼티 | 역할 |
|---|---|---|---|
| `EngineService` | `engine` | `${arms.engine.url}` | ALM 이슈 CRUD · ES 적재 · 서버/계정 검증 · Atlassian 동기화 |
| `AggregationService` | `engine-dashboard` | `${arms.engine.url}` (동일) | 대시보드·분석(cost/resource/scope/time/top-menu) 집계 |
| `AiService` | `ai-client` | `${arms.ai.url}` | `/performance/generate`, `/performance/analysis`, `/performance/analysis-script` |
| `MiddleProxyService` | `middle-proxy` | `${arms.middle-proxy.url}` | WBS·요구사항정의서 업로드 락/발행, 상태 매핑, POC 등록 |
| `GlobalConfigService` | `global-config` | `${arms.global-config.url}` | `/system-info/org-link` |
| `GotenbergClientService` | (config 별도) | — | PPTX/HTML → PDF 변환 |
| `InternalService` | `loopback` | **`http://127.0.0.1:31313`** (하드코딩) | 자기 자신 재호출 (동적 테이블 라우팅용) |
| `TemplateInternalService` | `template-loopback` | **동일** | 리포트 템플릿 스트림/해석 |

### 규칙

- **OpenSearch·Jira·Redmine 에 직접 붙지 않는다.** 전부 Engine-Fire 책임이다.
  새 검색·집계가 필요하면 Engine-Fire 에 엔드포인트를 요청하고 여기서는 Feign 시그니처만 추가한다.
- 전역 타임아웃(`OpenFeignConfig`): **connect 30초 / read 60분**, redirect follow.
  읽기 타임아웃이 60분이므로 "타임아웃이 나요"는 대부분 상대 서비스나 게이트웨이 쪽 문제다.
- 파라미터 형태: 쿼리는 `@RequestParam` / `@SpringQueryMap`, 바디는 `@RequestBody`,
  경로는 `@PathVariable`. multipart 는 `feign-form` 의존성이 들어있다.
- **`EngineService` 와 `AggregationService` 의 메서드·DTO 는 한글명이 많다**
  (`이슈_생성하기`, `증분이슈수집RequestDTO`, `지라이슈_데이터`). 기존 관례이므로 유지한다.
  호출 전 IDE 자동완성이 아니라 **파일을 직접 열어 정확한 이름을 확인**한다.
- Engine-Fire 경로/응답이 바뀌면 여기 시그니처도 함께 바꾸고
  `docs/ai/09_api_contract/backend-core-api-contract.md` 를 갱신한다.
- `MiddleProxyFeignConfig`(SESSION 쿠키 전달 인터셉터)는 **현재 어느 클라이언트에도 연결돼 있지 않다.**
  주석대로 보류 상태다. 쓰려면 `@FeignClient(configuration = MiddleProxyFeignConfig.class)` 를 명시해야 한다.

---

## 2. Kafka — REQADD 순차 소비

설정: `com/arms/config/KafkaConfig.java` (`@EnableKafka`, `@RefreshScope`)
`Application` 은 `@SpringBootApplication(exclude = KafkaAutoConfiguration.class)` 로 **자동설정을 끄고** 직접 구성한다.

```
Middle-Proxy ──produce──> topic REQADD ──> ReqAddConsumer
                                              └ ReqAddConsumerService.parse() / process()
                                                    └ InternalService (loopback HTTP) ──> ReqAddController
```

핵심 설정:

| 항목 | 값 | 이유 |
|---|---|---|
| `concurrency` | **1** | 토픽 내 순차 처리 보장 |
| `MAX_POLL_RECORDS` | **1** | 한 번에 1건만 |
| `AckMode` | **MANUAL** | 처리 완료 후 명시적 커밋 |
| 재시도 | `ExponentialBackOffWithMaxRetries(3)` | 소진 시 recoverer → DLT |
| DLT 토픽 | `${spring.kafka.topic.reqadd-dlt:REQADD-DLT}` (partitions 1 / replicas 1) | `ReqAddDltRecoverer` |

메시지 포맷(Key = `changeReqTableName`):
```json
{ "operation":"ADD_NODE|UPDATE_NODE|REMOVE_NODE|MOVE_NODE|UPDATE_DATABASE|UPDATE_DATE|
                UPDATE_REQADD_TITLE|UPDATE_ALL_REQADD_STATE|ADD_NODE_SKIP_ALM",
  "method":"POST|PUT|DELETE", "changeReqTableName":"T_ARMS_REQADD_12",
  "payload":"{...원본 JSON...}", "timestamp":1234567890, "requestId":"uuid" }
```

주변 구성요소:
- `kafka/callback/` — `ReqAddCallbackHandler` 구현체들(`ReqDef`, `Wbs`, `PocReq`). 빈 이름으로 맵 주입되어
  `fromAPI` 값에 따라 분기한다. 새 업로드 소스를 붙일 때 여기에 핸들러를 추가한다.
- `KafkaLagMonitor` / `KafkaShutdownManager` / `KafkaMonitorController`(`/kafka`) — lag 관측·graceful shutdown.
- `KafkaRetryableException` + `retryableKeywords`(`JDBCConnectionException`, `TransactionException`)
  → 이 키워드가 들어간 실패만 재시도 대상으로 본다.

**하지 말 것:** `concurrency`·`MAX_POLL_RECORDS` 를 성능 목적으로 올리지 않는다.
nested-set 트리는 순서가 깨지면 `c_left`/`c_right` 가 망가진다.

---

## 3. DWR (실시간 푸시)

- `DwrConfig` 가 `/dwr/*` 에 `DwrServlet` 을 등록하고, 설정은 `resources/dwr.xml`.
- 커스텀 `ScriptSessionManager` 사용 (`treeframework/remote/`).
- 업무 코드에서는 `Chat` 빈을 주입해 `chat.sendMessageByEngine("메시지")` 로 브로드캐스트한다.
- 메서드 단위로 자동 알림을 붙이려면 AOP 애노테이션을 쓴다:
  ```java
  @DwrSendAlarm(messageOnStart = "요구사항 생성 시작", messageOnEnd = "요구사항 생성 완료")
  ```
  `DwrSendAdvice` 가 `@Before`/`@AfterReturning` 으로 처리하고, 예외는 삼킨다(알림 실패가 업무를 막지 않음).
- 같은 계열 AOP: `@SlackSendAlarm`(`SlackSendAdvice`), `@MailSendAlarm`/`@MailSendErrorAlarm`(`MailSendAdvice`),
  `LoggingAdvice`. 모두 `com/arms/api/util/aspect/`.

---

## 4. Slack · 메일

- `SlackConfig` + `SlackNotificationService` + `SlackProperty.Channel`(`backend` 등).
  `ErrorControllerAdvice.onBaseException` 이 **모든 `BaseException` 을 Slack 으로 보낸다** —
  `BaseException` 계열을 남발하면 채널이 시끄러워진다.
- 메일: `spring-boot-starter-mail` + Thymeleaf 템플릿(`resources/templates/mail.html`, `templates/poc/*.html`).
  `api/report/mail/` 에 발송/수신 로그 도메인이 있다.

---

## 5. 스케줄러 — 이 서비스 안에 `@Scheduled` 는 없다

`src/main/java` 전체에 `@Scheduled`·`@EnableScheduling` 이 **하나도 없다.**
대신 **외부(Middle-Proxy 등)가 HTTP GET 으로 트리거**한다:

| 엔드포인트 (`/arms/scheduler`) | 하는 일 |
|---|---|
| `/pdservice/reqstatus/executeSequentialSchedules/storeToES` | 전체 이슈 수집 → ES |
| `/pdservice/reqstatus/increment/executeSequentialSchedules/storeToES` | 전일 증분 수집 |
| `…/storeToES/withDateRange?startDate&endDate` | 기간 지정 증분 수집 |
| `/pdservice/reqstatus/updateFromES` | ES → REQSTATUS 동기화 |
| `/pdservice/reqstatus/recreateFailedReqIssue` | 생성 실패 ALM 이슈 재생성 |
| `PUT /cacheStatusMappingData` | 상태 매핑 Redis 캐싱 |
| `/atlassian/directory-user/sync` | Atlassian 디렉토리 사용자 동기화 |

즉 **"주기 실행"을 추가해 달라는 요청은 여기에 `@Scheduled` 를 다는 것이 아니라,
엔드포인트를 만들고 호출자(Middle-Proxy/외부 스케줄러)에 등록을 요청하는 것**이다.
그 사실을 사용자에게 먼저 알린다.

`api/util/dynamicscheduler/` 의 `SchedulerType` enum 이 작업 종류를 정의한다
(`REQUIREMENT_ISSUE_BULK_SAVE`, `INCREMENTAL_ISSUE_BULK_SAVE`, `SYNC_REQ_STATUS_FROM_ES`,
`RECREATE_FAILED_ISSUE` 등).

---

## 6. 비동기 실행

- `Application` 에 `@EnableAsync`.
- `ThreadPoolConfig` 의 `taskExecutor-arms`: core 5 / max 10 / queue 10 / `CallerRunsPolicy`.
  **작은 풀이다.** 대량 병렬 작업을 여기에 얹으면 호출 스레드가 직접 실행(CallerRuns)하며 요청이 막힌다.
- `@Async` 스레드에는 **`RequestContextHolder` 가 없다** → `SessionUtil` 사용 불가 →
  동적 테이블에 접근해야 하면 `InternalService` loopback 을 쓴다.

---

## 7. 인증 / CORS

- Backend-Core 자체에는 Spring Security 필터체인 구성이 없다(`spring-security-web`,
  `keycloak-spring-security-adapter` 의존성만 존재). **인증·인가는 Middle-Proxy 가 처리**한다.
- `WebConfig` 는 `@RefreshScope` 로 `${cors.allowed-origins}` 를 읽어 `/**` 에 CORS 를 건다.
  값은 Config Server 에서 온다.
- 따라서 컨트롤러에 `@PreAuthorize`·`hasRole` 을 새로 넣지 않는다. 권한은 게이트웨이 경로 규칙이다.
