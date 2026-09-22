---
name: middleproxy-expert
description: >-
  A-RMS API 게이트웨이 저장소(Java-Service-Tree-Framework-Middle-Proxy)의 작업 규약.
  Spring Boot 2.6 · Java 11 · Spring Cloud Gateway(WebFlux) 기반이며 Backend-Core(MVC·JPA)와
  규칙이 전혀 다르다. 게이트웨이 라우트 · Keycloak OIDC 인증 · Redis 세션 · Kafka(REQADD) 발행 ·
  Redis 자체 도메인(aichat · wbs/reqdef 엑셀업로드 · wiki 락 · mapping · poc · atlassian · keycloak) ·
  Feign(백엔드코어통신기 · 엔진통신기)을 건드릴 때 반드시 먼저 읽을 것.
  SecurityConfiguration · pathMatchers · /auth-user · /auth-admin · RewritePath · @RedisHash ·
  @RedisEntity · AbstractRedisHashRepository · CustomRedisTemplate · setIfAbsent 락 ·
  ReqAddKafkaMessage · ADD_NODE · changeReqTableName · RequestBodyExtractor · Schedulers.boundedElastic ·
  Swagger2Config · 업로드 락이 안 풀림 · 콜백이 안 옴 같은 주제도 대상이다.
  "미들프록시", "middle proxy", "게이트웨이", "프록시 서버", "REQADD" 요청도 여기서 시작한다.
  MVC(HttpServletRequest · WebSecurityConfigurerAdapter · @Transactional · JPA)로 작성하지 않는다 —
  이 저장소는 전부 리액티브다.
---

# A-RMS Middle-Proxy 작업 규약

대상 저장소: `Java-Service-Tree-Framework-Middle-Proxy/`
(워크스페이스 루트 `C:\DEV\Project\Java-Service-Tree-Framework` 하위, 중첩 git 저장소 · 브랜치 `dev`)

이 저장소는 **A-RMS 전체 트래픽의 진입점**이다. 게이트웨이이면서 동시에 자체 REST 도메인과
Redis 저장소, Kafka 프로듀서를 겸한다. 잘못 손대면 특정 화면 하나가 아니라 **전 서비스가 막힌다.**
아래 계약을 먼저 파악하는 것이 이 저장소에서 가장 비용이 싼 길이다.

---

## 0. 30초 요약 — 반드시 먼저 각인할 것

| 항목 | 값 |
|------|----|
| 스택 | Spring Boot **2.6.15** · Spring Cloud **2021.0.9** · **Java 11** · Gradle 7.6.4 |
| 웹 모델 | **Spring WebFlux (리액티브)** — Spring Cloud Gateway |
| 영속 | **Redis 전용** (RDB·JPA·MyBatis 없음). 세션도 Redis |
| 메시징 | Kafka **Producer 전용** (토픽 `REQADD`). Consumer 는 Backend-Core |
| 인증 | Keycloak OIDC (realm `master`) + Spring Security WebFlux |
| 포트 | 13131 · Swagger `/middle-proxy-api/swagger-ui/` |
| 설정 | 대부분 **Spring Cloud Config(Global-Config)가 주입** — 저장소 yml 은 4줄짜리 뼈대뿐 |

> 루트 `README.md` 가 같은 요약을 담고 있다(2026-09-22 코드 기준으로 재작성됨).
> 버전 사실이 의심되면 언제나 `build.gradle` 이 정본이다.

### 이 저장소에서 쓰면 안 되는 것

```
✗ HttpServletRequest / HttpServletResponse      → ✓ ServerHttpRequest / ServerWebExchange
✗ WebSecurityConfigurerAdapter / HttpSecurity   → ✓ ServerHttpSecurity (@EnableWebFluxSecurity)
✗ @Transactional / JPA Entity                   → ✓ Redis 레포지토리 (§4)
✗ RedisTemplate 직접 호출                        → ✓ 도메인의 레포지토리 경유
✗ 컨트롤러에서 값 직접 반환                       → ✓ Mono<...> / Flux<...>
✗ 이벤트 루프에서 블로킹 호출                     → ✓ subscribeOn(Schedulers.boundedElastic())
```

---

## 1. 요청이 어디로 가는지 먼저 판별한다

들어온 경로는 **둘 중 하나**다. 어느 쪽인지 모르면 엉뚱한 파일을 고친다.

```
Frontend ──▶ Middle-Proxy :13131
                │
                ├─(A) 게이트웨이 통과 → Backend-Core / Engine-Fire / AI / Global-Config
                │     라우트는 이 저장소에 없다. Global-Config 주입 yml 의
                │     spring.cloud.gateway.routes 에 정의된다.
                │
                └─(B) 자체 컨트롤러가 직접 처리 → Redis 또는 Kafka
                      src/main/java/com/arms/api/<domain>/controller/
```

**(B)에 해당하는 자체 도메인 지도** (실제 `@RequestMapping` 기준)

| 도메인 | 경로 | 하는 일 | 저장 |
|--------|------|---------|------|
| `aichat` | `/auth-user/api/aichat/**` | AI 챗 대화방·메시지·RAG 문서·추천카드 | Redis(방식 B) |
| `kafka/reqadd` | `/kafka/reqAdd/**`, `/auth-user/api/arms/reqAdd/{sync,async}/**` | 요구사항 변경 Kafka 발행 | Kafka |
| `wbs` | `/wbs/**` | 간트/WBS 엑셀 업로드·콜백 | Redis(방식 A) |
| `reqdef` | `/req-def/**` | 요구사항정의서 엑셀 업로드·콜백 | Redis(방식 A) |
| `wiki` | `/wiki/lock/**` | 위키 문서 편집 분산 락 | Redis(Lua) |
| `mapping` | `/mapping/**` | ALM 이슈상태 ↔ A-RMS 상태 카테고리 | Redis(방식 A) |
| `pocreqregister` | `/poc/req-register/**` | PoC 요구사항 등록 | Redis(방식 A) + Kafka |
| `atlassian` | `/atlassian/directory-user/**` | Atlassian 계정 이메일 캐시(AES 암호화, 3일) | Redis(방식 A) |
| `keycloak` | `/auth-admin/**`, `/auth-user/**` | Keycloak Admin/User REST | Keycloak |
| `scheduler/dynamic` | `/auth-user/schedules/simulate` | cron 시뮬레이션 | - |

> `aichat` 이 `/auth-user/api/...` 를 쓰는 이유: 게이트웨이가 `/auth-user/api/(path)` → `/${path}` 로
> RewritePath 하기 때문에, 프론트는 다른 백엔드 호출과 동일한 접두를 쓰고 인증도 동일하게 걸린다.

---

## 2. 리액티브 규칙 (이 저장소의 핵심 계약)

### 2.1 컨트롤러는 `Mono`/`Flux`를 반환한다

```java
@RestController
@RequestMapping("/auth-user/api/aichat")
@RequiredArgsConstructor
@Slf4j
public class AiChatController {

    private final AiChatService aiChatService;

    @GetMapping("/rooms")
    public Mono<ResponseEntity<List<ChatRoom>>> getRoom(@AuthenticationPrincipal OidcUser oidcUser) {
        String userId = oidcUser.getPreferredUsername();          // 사용자 식별의 표준
        return Mono.fromCallable(() -> aiChatService.findRoomByUserId(userId))
                .subscribeOn(Schedulers.boundedElastic())          // ← 블로킹 격리 (필수)
                .map(ResponseEntity::ok);
    }
}
```

### 2.2 블로킹은 반드시 격리한다

Redis · Kafka · Feign · 파일 IO 는 전부 블로킹이다. Netty 이벤트 루프에서 직접 부르면
**부하 시 전 서비스가 멎는다.**

| 상황 | 감싸는 법 |
|------|----------|
| 값을 반환 | `Mono.fromCallable(() -> ...).subscribeOn(Schedulers.boundedElastic())` |
| 반환 없음 | `Mono.fromRunnable(() -> ...).subscribeOn(Schedulers.boundedElastic()).then(...)` |
| 오래 걸리는 파이프라인 전체 | 서비스 메서드에 `@Async` (`Application` 에 `@EnableAsync` 있음) |

`@Async` 는 wbs/reqdef 업로드처럼 "요청은 즉시 응답하고 뒤에서 오래 도는" 흐름에 쓴다
(`WbsServiceImpl.saveAllThenGetWbsRowVOS`, `ReqDefServiceImpl.saveReqDefUpload`).

### 2.3 요청 본문이 동적이면 `RequestBodyExtractor`

`@RequestBody` DTO 로 못 받는 경우(폼 인코딩 · 스키마가 테이블마다 다름)에 쓴다.
`application/x-www-form-urlencoded` 를 JSON 문자열로 바꿔준다.

```java
return requestBodyExtractor.extract(request)       // ServerHttpRequest
        .flatMap(payload -> service.publishToKafka("ADD_NODE", "POST", table, payload));
```

### 2.4 응답과 에러

- 정상: `CommonResponse.success(...)` → `ApiResult<T>` (`{success, response, error}`)
- 에러: 컨트롤러에서 임의 포맷을 만들지 않는다. `BaseException` 계열을 던지고
  `ErrorControllerAdvice` 가 `ErrorCode` 로 변환한다. 미처리 예외는 Slack 알림까지 간다.
- WebFlux 레벨(라우팅 실패·게이트웨이 에러)은 `GlobalErrorWebExceptionHandler`(`@Order(-2)`)가
  Accept 헤더를 보고 JSON 또는 빈 본문 + 상태코드만 반환한다(Whitelabel 제거, Nginx 가 에러 페이지 담당).

상세: `references/webflux-and-conventions.md`

---

## 3. 게이트웨이 · 보안은 항상 짝으로 판단한다

### 3.1 라우트는 이 저장소에 없다

`spring.cloud.gateway.routes` 는 **Global-Config 서버가 주입**한다
(dev `www.313.co.kr:33133`, stg/live `global-config:33133`).
저장소 안에서 아무리 찾아도 없다. 라우트 변경이 필요하면 **코드에 하드코딩하지 말고
Global-Config 변경이 필요하다는 점을 사용자에게 명시**한다.

### 3.2 실제 권한 표 (`config/security/SecurityConfiguration` 정본)

| 경로 | 접근 |
|------|------|
| `/login`, `/middle-proxy-api(/**)`, `/backend-core-api(/**)`, `/engine-fire-api(/**)`, `/actuator/**` | permitAll |
| `/mapping/**`, `/poc/**`, `/wbs/**`, `/req-def/**`, `/wiki/lock/**`, `/atlassian/**` | permitAll (내부 호출 전용) |
| `/auth-anon/**` | permitAll |
| `/dwr/**`, `/auth-user/**` | USER · MANAGER · ADMIN |
| `/auth-manager/**` | MANAGER · ADMIN |
| `/auth-admin/**` | ADMIN |
| **그 외 전부** (`/kafka/**` 포함) | 인증 필요 |

> `docs/ai/09_api_contract` §3 에 같은 표가 선언 순서까지 담겨 있다(2026-09-22 코드 기준으로 교정됨).
> 표가 의심되면 `SecurityConfiguration` 을 직접 읽는다 — 코드가 정본이다.

### 3.3 새 경로를 추가할 때 체크리스트

1. 이 저장소가 직접 처리하는가, 다운스트림으로 넘기는가? → §1
2. 다운스트림이면 Global-Config 라우트(`Path` 예측자 + `uri` + `RewritePath`) 필요.
3. 인증이 필요하면 `SecurityConfiguration.pathMatchers` 에 **role 도** 추가.
4. 내부 호출 전용(다른 모듈이 찌르는 API)이면 permitAll 그룹에 추가하되,
   **인터넷에 노출되면 안 되는 경로인지** 반드시 판단한다(현재 permitAll 목록은 내부망 전제다).
5. `pathMatchers` 는 **위에서부터 먼저 매칭**된다. `/auth-user/**` 보다 구체적인 규칙은 그 앞에 둔다.

상세: `references/gateway-and-security.md`

---

## 4. Redis — 두 방식, 절대 섞지 않는다

이 저장소에는 Redis 접근 방식이 **두 가지** 있다. 도메인마다 하나만 쓴다.

### 방식 A — Spring Data Redis (`@RedisHash`)

```java
@RedisHash("pocReqRegister")            // 키스페이스
public class PocReqRegisterVO { @Id private String id; /* ... */ }

public interface PocReqRegisterRepository extends CustomRedisTemplate<PocReqRegisterVO, String> {}
```

`CustomRedisTemplate` 은 `CrudRepository` + 이 저장소가 추가한 기능이다.
구현체는 `BaseRedisRepository` (`RedisConfig` 의 `@EnableRedisRepositories(repositoryBaseClass=...)`).

| 추가 기능 | 용도 |
|----------|------|
| `scan(pattern)` · `deleteByPattern(pattern)` | `keySpace:pattern` 으로 SCAN. **`findAll()` 대신 이걸 쓴다** |
| `setIfAbsent(subKey, value, ttl)` | 분산 락 획득 (SET NX PX) |
| `deleteIfEquals` · `expireIfEquals` | 토큰이 일치할 때만 해제/연장 (Lua, 원자적) |
| `deleteIfFieldEquals` · `expireIfFieldEquals` · `setFieldIfFieldEquals` | 값이 JSON 일 때 특정 필드 비교 후 조작 (Lua) |
| `deleteIfFieldOlderThan` | 유휴 시간 초과 시 강제 해제 (위키 락 takeover) |

### 방식 B — 커스텀 Redis Hash 프레임워크 (`api/util/redisrepo`)

`aichat` 전용. 엔티티에 어노테이션을 붙이고 `AbstractRedisHashRepository` 를 상속하면 CRUD 가 생긴다.

```java
@RedisEntity(value = "ai:chat:room", ttlDays = 30)
public class ChatRoom {
    @RedisId    private String roomId;
    @RedisScore private long   updatedAt;     // 정렬 기준(선택)
    private String title;                      // 단순 타입 → 문자열로 저장
    private List<String> pdServiceVersionIds;  // 복합 타입 → JSON 으로 저장
}

@Repository
public class ChatRoomRepository extends AbstractRedisHashRepository<ChatRoom, String> {
    public ChatRoomRepository(RedisHashRepository r, ObjectMapper m) { super(r, m, ChatRoom.class); }
}
```

키 구조: `{namespace}:{id}` → Hash, `{namespace}:index` → Hash `{id: score}`.

### 키스페이스 전체 지도

| 키스페이스 | 방식 | 엔티티 | 비고 |
|-----------|------|--------|------|
| `ai:chat:*` | B | ChatRoom · ChatRoomList · ChatMessageList · RagDocs · LastSelection · RecommendedCard | TTL 30일 |
| `excelUpload` | A | **ExcelUploadFileVO · WbsRowVO · ReqDefRowVO (3종 공유!)** | id 접두로 구분 |
| `almIssueStatus` · `state` · `category` | A | mapping 도메인 | |
| `pocReqRegister` | A | PocReqRegisterVO | |
| `atlassian` | A | AtlassianDirectoryUserEntity | `timeToLive` 3일, email AES256 암호화 |
| `wiki:lock` | A(Lua) | LockHolder | 값은 JSON 문자열 |
| `spring:session:sessions:*` | Spring Session | - | `maxInactiveInterval` 2시간 |

> ⚠️ **`excelUpload` 키스페이스는 3개 타입이 공유한다.** id 접두로만 구분된다
> (`wbs:{pdServiceId}:{wbs}:{jobName}`, `reqdef:{pdServiceId}:{classLevelKey}`,
> `lock:wbs:{pdServiceId}`, `lock:reqdef:{pdServiceId}`).
> 그래서 `findAll()` 을 부르면 타입이 섞여 깨진다. **반드시 `scan(pattern)` + `findAllById`** 를 쓴다.

상세: `references/redis-data-model.md`

---

## 5. Kafka — REQADD 프로듀서

```
Frontend/내부도메인 → Middle-Proxy (Producer)
    kafkaTemplate.send("REQADD", changeReqTableName, ReqAddKafkaMessage(JSON))
        → Kafka (파티션 1개, 순서 보장)
            → Backend-Core (@KafkaListener, operation 분기) → DB
```

- 토픽 `REQADD`: **partitions 1** (순서 보장 의도). replicas 3, retention 4주.
  늘리면 요구사항 변경 순서가 깨진다.
- 메시지 키 = `changeReqTableName` (= `T_ARMS_REQADD_{pdServiceId}`).
- 프로듀서: `acks=all`, `retries=3`, `enable.idempotence=true`, `lz4`.
- Kafka 빈은 `config/KafkaConfig` 에서 **수동 정의**. `Application` 이 `KafkaAutoConfiguration` 을 제외한다.
- 발행 후 응답은 **`ACCEPTED` 성격**(`status: ACCEPTED` + `requestId`). 처리 완료가 아니다.

현재 쓰이는 `operation` 값: `ADD_NODE` · `UPDATE_NODE` · `REMOVE_NODE` · `MOVE_NODE` ·
`UPDATE_DATABASE` · `UPDATE_DATE` · `UPDATE_REQADD_TITLE` · `UPDATE_ALL_REQADD_STATE` · `ADD_NODE_SKIP_ALM`.

> ⚠️ **operation 을 추가/변경하면 Backend-Core Consumer 의 switch 도 함께 고쳐야 한다.**
> 이 저장소만 고치면 메시지가 조용히 버려진다(에러도 안 난다).

상세: `references/kafka-reqadd.md`

---

## 6. 엑셀 업로드 파이프라인 (wbs · reqdef) — 이 저장소에서 가장 복잡한 흐름

```
①  POST /req-def/pd-service-id/{id}/lock     → setIfAbsent (TTL 5분) → uploadToken 발급
②  POST /req-def                              → @Async 시작, 즉시 응답
③  Redis 에 행 전량 교체 (replaceAll)         → 무효 서브트리 종결
④  백엔드코어통신기.ganttExcelUploadRefresh   → 화면 갱신 알림
⑤  루트(ref=2) 행만 Kafka 발행                → markRequestComplete
⑥  Backend-Core 가 노드 생성 후 콜백
    POST /req-def/publish-kafka-from-parent-node
⑦  markConsumed → 락 갱신(renew) → 자식 행 발행 → ⑥ 반복 (트리 깊이만큼)
⑧  더 처리할 행이 없으면(drain) 락 해제
    → pruneEmptyFoldersFromUpload → excelUploadComplete
```

핵심 규칙:

- 행 상태는 `valid` / `requestComplete`(발행함) / `consumeComplete`(콜백 받음) / `failed` 로 관리된다.
  `isTerminated() = !valid || consumeComplete || failed`.
- **락 해제는 오직 드레인 판정에서만** 한다(`releaseLockIfDrained`). 중간에 풀면 동시 업로드가 섞인다.
- 콜백의 `uploadToken` 이 현재 행의 토큰과 다르면 **이전 업로드의 지각 콜백**이므로 무시한다.
- `reqdef` 는 MOVE 를 UPDATE 보다 **먼저** 발행한다. 순서를 바꾸면 빈 분류 정리가 오판한다.
- 실패하면 하위 서브트리 전체를 `cascadeUnreachable` 로 종결시킨다(무한 대기 방지).

상세: `references/domains.md` §wbs · §reqdef

---

## 7. 외부 통신 (Feign)

| 인터페이스 | 대상 | URL |
|-----------|------|-----|
| `백엔드코어통신기` | Backend-Core | `${arms.backend.url}` |
| `엔진통신기` | Engine-Fire | `${arms.engine.url}` |
| `내부통신기` | 자기 자신(loopback) | `http://127.0.0.1:13131` (하드코딩) |

> ⚠️ **Feign 에 Encoder 가 없다.** `FeignResponseDecoderConfig` 는 Decoder 만 등록한다.
> WebFlux 라 `HttpMessageConverters` 가 자동 구성되지 않으므로 **`@RequestBody` 를 쓰면 런타임에 깨진다.**
> 기존 코드처럼 `@RequestParam` / `@PathVariable` 로 보낸다
> (`백엔드코어통신기.pruneEmptyFoldersFromUpload` 의 주석이 이 사실을 못박고 있다).
> 기본 timeout 은 connect/read 180초(설정 주입).

---

## 8. 실행해서 확인하기

```bash
# 컴파일만 (가장 빠른 검증)
./gradlew compileJava            # Windows: gradlew.bat compileJava

# 로컬 구동: Active Profile = dev, 포트 13131
#   Redis 는 저장소 동봉 바이너리로 띄울 수 있다
./Redis-x64-3.2.100/redis-server.exe ./Redis-x64-3.2.100/redis.windows.conf
```

- Swagger: `http://127.0.0.1:13131/middle-proxy-api/swagger-ui/`
- Actuator: `/actuator/{health,env,beans,httptrace,refresh}` (permitAll — 노출 주의)
- `./gradlew build` 는 Nexus 메타데이터(`metadata.xml`) 조회에 의존해 오프라인에서 실패할 수 있다.
- 테스트는 `WbsServiceImplTest` 1건뿐이고 `@SpringBootTest` + Redis/Config 서버 기동을 전제한다.
  새 로직은 가능하면 스프링 컨텍스트 없는 순수 단위 테스트로 검증한다.

---

## 9. 제출 전 자가 점검

- [ ] 컨트롤러가 `Mono`/`Flux` 를 반환하는가? Servlet 타입을 쓰지 않았는가?
- [ ] Redis·Kafka·Feign 호출을 `boundedElastic` 으로 격리했는가?
- [ ] 새 경로를 만들었다면 `SecurityConfiguration.pathMatchers` 를 반영했는가?
      (라우트가 필요하면 Global-Config 변경 필요를 보고했는가?)
- [ ] Redis 접근을 도메인의 기존 방식(A 또는 B)으로 통일했는가? `RedisTemplate` 직접 호출은 없는가?
- [ ] `excelUpload` 키스페이스를 건드렸다면 `findAll()` 대신 `scan()` 을 썼는가?
- [ ] Kafka `operation` 을 늘렸다면 Backend-Core Consumer 동반 변경을 명시했는가?
- [ ] 락을 잡는 경로에서 **모든 실패 경로**에 해제가 보장되는가?
- [ ] 시크릿(`aes.token` · `slack.token` · `client-secret`) 값을 코드·로그·문서에 복제하지 않았는가?
- [ ] Boot 2.6 / Java 11 에서 쓸 수 있는 API 만 썼는가? (`jakarta.*` · Java 17 문법 금지)
- [ ] 로그에 사용자 식별자·요청 ID 를 남겨 추적 가능한가? (`[PERF]` · 이모지 접두 관례)

---

## 10. 산출 및 인계

- 사용자 대상 설명은 **한국어**로 한다.
- **commit·push 하지 않는다.** 작업 요약과 커밋 메시지 초안만 제시하고 커밋은 사용자가 한다.
  이 저장소의 실제 컨벤션(YouTrack 연동):
  ```
  feat : [ARMS-1189] #comment✅패스워드 이메일 설정 처리 2026.09.11 #close #time 1h +review SR @sevoon0909
  fix : [ARMS-1195] #comment✅문서 저장시 락 해제 안되는 문제 2026.09.10 #close
  refactor : [ARMS-1189] #comment✅컨트롤러에 로직을 서비스로 옮김 2026.09.08 #close
  ```
  현재 작업 브랜치는 `dev` 다(`main` 아님).
- 확신이 없는 지점(Global-Config 실제 라우트 값, 다운스트림 응답 스펙, Consumer 동작)은
  추측으로 메우지 말고 **가정을 명시**하거나 질문한다.

---

## 11. 참조 파일 지도

| 파일 | 언제 읽나 |
|------|----------|
| `references/webflux-and-conventions.md` | 컨트롤러·서비스를 쓸 때. 리액티브 패턴·응답·에러·AOP·네이밍 |
| `references/gateway-and-security.md` | 라우트·권한·로그인/로그아웃·세션·필터를 건드릴 때 |
| `references/redis-data-model.md` | Redis 저장 구조·커스텀 프레임워크 API·락·Lua 를 쓸 때 |
| `references/kafka-reqadd.md` | REQADD 발행·메시지 포맷·operation 을 다룰 때 |
| `references/domains.md` | 특정 도메인(aichat · wbs · reqdef · wiki · mapping · poc · atlassian · keycloak) 작업 시 |
| `references/integration-and-ops.md` | Feign · Slack · Swagger · 빌드 · Docker · 배포 · 모니터링 |
| `references/pitfalls.md` | 이상 동작이 보일 때 / 착수 전 함정 확인 |

저장소 자체 문서 `Java-Service-Tree-Framework-Middle-Proxy/docs/ai/` 도 살아 있는 보조 정본이다
(`harness_engineering.md` 가 지도, `12_known_issues/guide.md` 에 함정 누적,
`06_domain_playbooks/` 에 gateway-routing · keycloak-auth · reqadd-kafka · excel-upload · aichat · wiki-lock).
**2026-09-22 에 코드 전수 대조로 정합화했다.** 작업 후 변경은 `11_changelog`,
새 함정은 `12_known_issues` 에 남긴다.

루트 문서 2종도 같은 날 코드 기준으로 재작성됐다 — `README.md`(아키텍처·로컬구동·빌드배포 요약),
`REQADD_KAFKA_INTEGRATION.md`(Producer 관점 Kafka 통합: operation 9종 · `fromAPI` ↔ Backend-Core
콜백 핸들러 빈 이름 계약 · 테스트 curl · 모니터링 · 에러 처리).

> 폐기 상태로 남겨둔 것(삭제는 사용자 몫): `06_page_playbooks/`,
> `06_domain_playbooks/issue-buffer.md`(해당 도메인이 소스에 없음).
