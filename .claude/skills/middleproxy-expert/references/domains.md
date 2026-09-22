# 도메인별 상세

패키지 기준: `src/main/java/com/arms/api/<domain>/`.
새 도메인을 만들 때는 **인접 도메인의 구조를 그대로 복제**한다(계층 배치가 도메인마다 다르다).

---

## aichat — AI 챗 (Redis 방식 B)

```
aichat/
├─ constant/AiChatRedisKeys      키 상수 · TTL 30일 · MAX_MESSAGES 20 · MAX_HISTORY 10
├─ controller/AiChatController           /auth-user/api/aichat
│            RecommendedCardController   /auth-user/api/aichat/recommended-cards
├─ domain/    ChatRoom · ChatRoomList · ChatMessage · ChatMessageList
│             RagDocs · LastSelection · RecommendedCard      (@RedisEntity)
├─ dto/       ChatRoomRequest · ChatRoomUpdateRequest · ChatMessageRequest
│             RagDocsRequest · LastSelectionRequest · CardContextItem
├─ init/      RecommendedCardInitializer(ApplicationRunner) · AiChatDataMigration
├─ repository/ *Repository extends AbstractRedisHashRepository
└─ service/   AiChatService(Impl) · RecommendedCardService(Impl)
```

엔드포인트:

| 메서드 | 경로 | 동작 |
|--------|------|------|
| POST | `/rooms` | 대화방 생성(중복 제목 해소, 10개 초과 시 가장 오래된 방 삭제) |
| PATCH | `/rooms/{roomId}` | 제품/버전 컨텍스트 갱신 |
| POST | `/rooms/{roomId}/messages` | 메시지 저장(최대 20개 유지) |
| PUT | `/rooms/{roomId}/messages/last-assistant` | 마지막 assistant 메시지 덮어쓰기 |
| GET | `/rooms`, `/rooms/{roomId}/messages` | 조회 |
| DELETE | `/rooms/{roomId}` | 방 삭제 |
| POST/GET/PATCH | `/rooms/{roomId}/rag-docs`(+`/summary`) | RAG 문서 저장·조회·요약 |
| GET | `/cards/context` | 추천 카드 컨텍스트 |
| POST/GET/DELETE | `/last-selection` | 사용자의 마지막 제품/버전 선택 |
| CRUD | `/recommended-cards`(+`/{cardId}`) | 추천 카드 관리 |

- 사용자 식별은 항상 `@AuthenticationPrincipal OidcUser` → `getPreferredUsername()`.
- 모든 서비스 호출을 `Mono.fromCallable/fromRunnable + boundedElastic` 으로 감싼다.
- `RecommendedCardInitializer` 가 기동 시 기본 카드 3개(Time/Scope/Resource)를 멱등 초기화한다.
  기본 카드 문구를 바꾸면 기존 카드가 전량 교체된다.
- 성능 로그 관례: `log.info("[PERF] ... | {}ms | ...", ...)`.

---

## kafka/reqadd — 요구사항 변경 발행

`references/kafka-reqadd.md` 참조.

---

## excelupload — wbs·reqdef 공통 기반

```
excelupload/
├─ model/enums/ExcelUploadFeature   WBS("wbs") · REQDEF("reqdef")
├─ model/vo/ExcelUploadFileVO       @RedisHash("excelUpload"), 업로드 파일 경로 보관
├─ repository/ExcelUploadRepository extends CustomRedisTemplate
└─ service/ ExcelUploadKey (키 조립) · ExcelUploadLock (락) · ExcelUploadPathService(Impl)
```

키 규칙:

```
excelUpload:{feature}:{pdServiceId}            ← 업로드 파일 경로
excelUpload:lock:{feature}:{pdServiceId}       ← 락 (값 = uploadToken UUID, TTL 5분)
```

---

## wbs — 간트/WBS 엑셀 업로드 (Redis 방식 A + Kafka)

```
wbs/
├─ controller/WbsController            /wbs
├─ model/dto/ServerDataDTO             엑셀 한 행의 원본 데이터(wbs 번호 · jobName · 담당자 · 일정 등)
├─ model/enums/WbsStatus               LEAF("등록 가능") · BRANCH("하위 항목 존재") · UNREACHABLE("상위 노드 누락")
│                                       treeType() → BRANCH 면 "folder", 아니면 "default"
├─ model/vo/ WbsRowVO · WbsRowId · WbsCallbackReqVO · ReqAddAndWbsRowVO · ReqAddTitleVO
├─ repository/WbsRepository
└─ service/ WbsService(Impl) · WbsRowNotifier
```

엔드포인트:

| 메서드 | 경로 |
|--------|------|
| POST | `/wbs` (업로드 시작, `@Async`) |
| POST/DELETE | `/wbs/pd-service-id/{pdServiceId}/lock` |
| GET | `/wbs/pd-service-id/{serviceId}` · `/wbs/pd-service-id/{serviceId}/id/{id}` |
| DELETE | `/wbs/pd-service-id/{serviceId}` |
| POST | `/wbs/publish-kafka-from-parent-node` (Backend-Core 콜백 수신) |
| POST/GET | `/wbs/pd-service-id/{pdServiceId}/upload` (파일 경로 저장·조회) |

행 id: `wbs:{pdServiceId}:{data.wbs}:{data.jobName}` (`WbsRowId`).
발행 시 `changeReqTableName = "T_ARMS_REQADD_" + pdServiceId`, `fromAPI = "gantt-excel-upload"`.
폴더 행의 긴급도/중요도/난이도는 엑셀에 없으므로 `DEFAULT_LEVEL_LINK = 5L`(보통)로 채운다.

---

## reqdef — 요구사항정의서 엑셀 업로드 (Redis 방식 A + Kafka)

```
reqdef/
├─ controller/ReqDefUploadController   /req-def
├─ model/dto/ReqDefDataDTO             엑셀 한 행(reqId · reqName · assignee · detail ...)
├─ model/vo/ ReqDefRowVO · ReqDefRowId · ReqDefRows(일급 컬렉션) · ReqDefRowChange
│            ClassLevelKey · ChangeReqTableName · ReqDefCallbackReqVO · ReqAddAndReqDefRowVO
├─ repository/ ReqDefRepository · ReqDefRowStore(파사드)
└─ service/ ReqDefService(Impl) · ReqDefNodePublisher · ReqAddPayloadFactory
            ReqAddNodeFinder · ReqDefRowNotifier
```

엔드포인트:

| 메서드 | 경로 |
|--------|------|
| POST/DELETE | `/req-def/pd-service-id/{pdServiceId}/lock` |
| POST | `/req-def` (업로드 시작, `@Async`) |
| GET | `/req-def/pd-service-id/{serviceId}` |
| POST | `/req-def/publish-kafka-from-parent-node` (콜백) |
| POST/GET | `/req-def/pd-service-id/{pdServiceId}/upload` |

핵심 개념:

- **`classLevelKey`** = 분류 경로를 `|` 로 이은 문자열(`대분류|중분류|요구사항명`).
  `ClassLevelKey.covers()` 로 조상/후손 판정, `depth()` 로 깊이 계산.
  행 id = `reqdef:{pdServiceId}:{classLevelKey}`.
- **`ReqDefRows`** 일급 컬렉션이 `branchFirst()` · `descendantsOf()` · `notTerminated()` ·
  `hasPendingWork()` · `previousParentIds()` 같은 판정을 담당한다. 루프를 새로 짜지 말고 여기에 추가한다.
- **`ReqAddNodeFinder`** 가 기존 노드를 찾는다: 리프는 `reqId` 로(`getReqAddByReqDefId`),
  브랜치는 부모 + 제목으로(`getReqAddByParentAndTitle`). 있으면 UPDATE/MOVE, 없으면 ADD.
- **`ReqAddPayloadFactory`** 가 payload 를 만든다.
  생성 시에만 버전셋·기본 리뷰어·기본 상태를 싣는다(수정에 실으면 사용자 지정 버전이 덮어써진다).
- **`ReqDefNodePublisher.updateAndMove`** 는 MOVE 를 먼저, UPDATE 를 나중에 발행한다(순서 바꾸지 말 것).
- `ReqDefRowNotifier` 가 `@Async` 로 행 단위 상태(`COMPLETE`/`FAILED`)를
  `백엔드코어통신기.reqDefRowStatus` 로 통지한다.
- 드레인 완료 시 `pruneEmptyFoldersFromUpload`(이동으로 비워진 분류 정리) →
  `excelUploadComplete`(전 구간 완료 알림) 순으로 호출한다.

---

## wiki — 문서 편집 분산 락

```
wiki/
├─ controller/WikiLockController   /wiki/lock/{acquire,release,renew,touch,force-release,snapshot}
├─ model/dto/ LockRequest · LockState (EVENT_ACQUIRED / EVENT_DENIED 등)
├─ model/vo/LockHolder             @RedisHash("wiki:lock") — 키스페이스 제공용 껍데기
├─ repository/WikiLockRepository
└─ service/WikiLockService         TTL 120초, takeover 유휴 60초
```

- 값은 Hash 가 아니라 **JSON 문자열**이다(`setIfAbsent`). 그래서 `deleteIfFieldEquals` 계열
  Lua 스크립트가 동작한다.
- 컨트롤러가 **동기 반환**(`LockState`, `boolean`)이다. 락 연산이 짧다는 전제.
- `acquire` 재진입 허용, 타인 보유 시 `DENIED` + 보유자 정보 반환.

---

## mapping — ALM 이슈 상태 ↔ A-RMS 상태 카테고리

```
mapping/
├─ controller/MappingController   /mapping
├─ domain/   AlmIssueStatus · State · StateCategory   (@RedisHash)
├─ dto/      AlmIssueStatusDTO · AlmServerRequestDTO · StateDTO · StateCategoryDTO
├─ repository/ ...Repository extends CustomRedisTemplate
├─ service/  AlmIssueStatusService · StateService · StateCategoryService
└─ vo/       StateMappingInfoResponse
```

| 메서드 | 경로 | 동작 |
|--------|------|------|
| POST | `/mapping/alm/issuestatus` | 서버/프로젝트/이슈타입 단위로 기존 키를 패턴 삭제 후 재등록 |
| POST | `/mapping/state` · `/mapping/category` | A-RMS 상태·카테고리 초기화 |
| GET | `/mapping/category?serverId=&...` | ALM 상태 → A-RMS 카테고리 조회 |
| POST | `/mapping/state-mapping-info` | 전체 매핑 정보 반환 |

키 규칙: `{serverId}-{projectKeyOrId}-{issueTypeId}-{issueStatusId}`.
빈 값은 압축되고 끝의 `-` 는 제거된다(둘 다 없으면 `{serverId}-{issueStatusId}`).
초기화 시 `pattern + "*"` 로 `deleteByPattern` 후 저장하므로, 키 규칙을 바꾸면
**옛 키가 고아로 남는다.**

---

## pocreqregister — PoC 요구사항 등록

```
pocreqregister/
├─ controller/PocReqRegisterController   /poc/req-register
├─ dto/ PocReqRegisterRequestDTO · PocReqStatusCallbackDTO
├─ repository/PocReqRegisterRepository
├─ service/PocReqRegisterService
└─ vo/PocReqRegisterVO                  @RedisHash("pocReqRegister")
```

| 메서드 | 경로 | 동작 |
|--------|------|------|
| POST | `/poc/req-register` | ALM 이슈들을 요구사항으로 등록 → Kafka `ADD_NODE_SKIP_ALM` 발행 |
| GET | `/poc/req-register` | 등록 현황 조회(Redis 만으로 표시하도록 이슈 제목·상태·작성자를 등록 시점에 함께 보관) |
| POST | `/poc/req-register/complete` · `/fail` | Backend-Core 처리 결과 콜백 |

`ADD_NODE_SKIP_ALM` 은 "ALM 이슈를 새로 만들지 말고 기존 이슈에 연결만 하라"는 의미의 operation 이다.
하나의 이슈 키에 여러 버전이 매핑될 수 있어 `pdServiceVersionLinks` 가 리스트다.

---

## atlassian — 계정 이메일 캐시

```
atlassian/
├─ controller/AtlassianDirectoryUserController   /atlassian/directory-user
├─ model/{dto,entity,vo}
├─ repository/AtlassianDirectoryUserRepository
└─ service/AtlassianDirectoryUserService(Impl)
```

| 메서드 | 경로 |
|--------|------|
| POST | `/store` (accountId → email 저장) |
| POST | `/{connectId}/email` (단건 조회) |
| POST | `/{connectId}/emails` (복수 조회) |

- 키: `atlassian:{connectId}:{accountId}`, `timeToLive` 3일.
- **email 은 `AES256`(AES/GCM/NoPadding, 랜덤 12바이트 IV)으로 암호화해 저장**하고 조회 시 복호화한다.
  키는 `aes.token` 설정값. 키가 비어 있으면 `encrypt` 가 평문을 그대로 돌려준다(주의).

---

## keycloak — 사용자·Realm 관리

```
keycloak/
├─ admin/controller/KeycloakAdminController     /auth-admin/**  (@RolesAllowed)
│  admin/service/KeycloakAdminUserService(Impl) · KeycloakPasswordPolicyService
│  admin/model/dto/CreateUserDTO
└─ user/controller/KeycloakUserController · UserController      /auth-user/**
   user/service/KeycloakUserService(Impl)
```

`KeycloakAdminController` 가 다루는 것: token · realm(+SMTP 설정/테스트) · client · group(+역할 매핑/멤버) ·
role · user 생성 · 비밀번호 재설정 · 사용자 목록.

`UserController`: `/auth-user/me` · `/auth-user/session-id` · `/auth-user/logout`.
`KeycloakUserController`: `/auth-user/search-user/{userName}` · `/auth-user/users` ·
`/auth-user/user/{user-id}/check-permission/{current-page}`.

비밀번호 정책 위반은 `PasswordPolicyNotMetException`(Keycloak 응답의 `"Password policy not met"` 판정),
중복 사용자는 `UserAlreadyExistsException`(409).

---

## scheduler/dynamic — cron 시뮬레이션

`POST /auth-user/schedules/simulate` — `SchedulerDTO` 를 받아 다음 실행 시각 목록을 돌려준다.
`MadCronExpression` · `CronLocalDateTimes` 사용, `@CronCheck` 가 10분 미만 주기를 거부한다.

실제 스케줄 실행은 이 저장소가 하지 않는다. Global-Config(`/auth-sche/**`)가 돌리고
`내부통신기` 가 loopback 으로 그 경로를 호출하는 구조다.

---

## util — 공통 기반

| 패키지 | 내용 |
|--------|------|
| `util/redisrepo` | 커스텀 Redis 프레임워크 (`references/redis-data-model.md`) |
| `util/communicate` | Feign 3종 (`references/integration-and-ops.md`) |
| `util/aspect` | `SessionParamAdvice`(전 컨트롤러 예외 훅) · `@LogAndSlackNotify` + Aspect |
| `util/aes` | `AES256`(GCM) · `AESProperty`(`aes.token`) |
| `util/slack` | `SlackNotificationService`(stg 프로파일에서만 발송) · `SlackProperty`(채널 `middleproxy`/`schedule`) |
| `util/cron` | `MadCronExpression` · `CronLocalDateTimes` |
| `util/validation` | `@CronCheck` + Validator, `group/ApplyNode` |
| `util/errors` | `BaseException` 계열 · `ErrorCode` · `ErrorControllerAdvice` |
| `util/response` | `CommonResponse` / `ApiResult` |
| `util/license` | `LicenseValidator` — **본문이 전부 주석 처리된 미사용 코드** |
| `util/RequestBodyExtractor` | WebFlux 요청 본문 → JSON 문자열 |
| `util/HighlightingCompositeConverterCustom` | logback 컬러 컨버터 |
