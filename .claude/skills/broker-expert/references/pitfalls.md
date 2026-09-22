# Broker-Hub 함정 모음

증상 → 원인 → 확인 지점 순서로 정리했다. **착수 전에 훑고, 이상 동작이 보이면 먼저 여기를 본다.**
모든 항목은 2026-09-22 기준 `dev` 브랜치 코드 대조로 작성했다.

---

## A. 동시편집

### A-1. 오래 편집한 문서가 사용자마다 다르게 보인다 ⚠️ 최우선

- **원인**: 리비전 = `LLEN history` 인데 Lua 가 500 개에서 `LTRIM` 한다.
  500 도달 후 리비전이 멈추고, `LRANGE clientRevision .. serverRevision-1` 의 인덱스가
  실제 리비전과 어긋난다 → 엉뚱한 op 로 transform → 내용 분기.
- **예외가 안 난다.** 로그만 봐서는 정상으로 보인다.
- **확인**: `LLEN doc:{sessionId}:history:{documentId}` 가 정확히 500 인지.
- **파일**: `OtService.MAX_HISTORY_SIZE_PER_DOC`, `RedisConfig.updateContentAndHistoryScript`.
- **고칠 때**: 리비전을 `INCR` 기반 별도 카운터로 분리 + 히스토리 인덱스 오프셋 보정.
  LTRIM 제거만 하면 메모리가 무한히 는다. **설계 판단이므로 사용자에게 보고할 것.**

### A-2. `Invalid client revision` 경고 후 편집이 반영되지 않는다

- **원인**: `clientRevision > serverRevision`. 클라이언트가 서버보다 앞선 리비전을 주장.
  `setDocumentContent`(= `POST /api/sessions/{id}/set-document`)가 히스토리를 **삭제**해
  리비전을 0 으로 되돌렸는데 클라이언트가 옛 리비전을 들고 있으면 발생한다.
- **동작**: `OtController` 가 `IllegalArgumentException` 을 잡아 `logger.warning` 만 남긴다.
  **클라이언트에는 아무것도 안 간다** — ACK 도 없고 에러 프레임도 없다. 조용히 사라진다.
- **확인**: 로그 `Invalid client revision: N. Server revision is: M`.

### A-3. `Both operations have to have the same base length`

- **원인**: 히스토리의 op 와 들어온 op 의 기준 문서 길이가 다르다.
  대개 A-1(트림) 또는 A-2(강제 내용 주입) 의 2차 증상이다.
- **파일**: `OtUtils.transform` 첫 줄 검증.

### A-4. `Operation did not consume the entire document.`

- **원인**: `apply()` 가 op 소비 후 문서 끝에 도달하지 못했다. op 의 `baseLength` 와 실제 문서 길이 불일치.
- **주의**: `OtService` 는 이 예외를 `RuntimeException` 으로 감싸지 않고 그대로 올려
  `OtController` 의 `catch (Exception)` 에서 `logger.severe` 로 끝난다. 역시 **클라이언트 무통보**.

### A-5. 내가 보낸 op 가 나에게도 다시 온다

- **사양이다.** `/topic/sessions/{sid}/operations/document/{did}` 에는 발신자 포함 전원에게 나간다.
  payload 의 `clientId` 로 클라이언트가 자기 것을 걸러야 한다.
  선택/커서(`/app/selection`) 도 동일하며, 프론트는 `response.userInfo.id !== self._userInfo.userId` 로 거른다.

---

## B. 세션 · 참가자

### B-1. 브라우저를 강제 종료했는데 참가자 목록에 계속 남는다 ⚠️ 최우선

- **원인**: `WebSocketEventListener.handleWebSocketDisconnectListener` 는
  `SimpMessageHeaderAccessor.getUser(headers)` 가 **null 이면 아무것도 하지 않는다.**
  이 저장소에는 Spring Security 도, `Principal` 을 주입하는 `HandshakeHandler` /
  `ChannelInterceptor` 도 없다 → 현재 구성에서 이 경로는 **사실상 죽은 코드**다.
- **현재 실제로 도는 정리 경로**: `/app/leave` 명시 호출, 그리고 `session:users:*` 키의 TTL 60분 만료.
- **확인**: 로그 `WebSocket Disconnected: No user principal found.` 가 찍히는지.
- **고칠 때**: 게이트웨이가 전달하는 사용자 식별자를 핸드셰이크 또는 STOMP CONNECT 헤더에서 읽어
  Principal 로 바인딩해야 한다. **설계 판단이므로 사용자에게 확인할 것.**

### B-2. 같은 이유로 락도 안 풀린다

- B-1 과 동일 원인. disconnect 시 `wikiLockService.release(..., REASON_DISCONNECT)` 가 호출되지 않는다.
- 다만 Middle-Proxy 락 TTL 이 120초라 **그 안에 자동 만료**된다. 영구 점유는 아니다.
- 관련 이력: 커밋 `1e180ff` "문서 저장시 락 해제 안되는 문제".

### B-3. `GET /api/sessions/{id}` 가 404

- **원인**: `SessionController.activeSessions` 는 `static ConcurrentHashMap` 이다.
  **재시작하면 전부 사라지고**, 인스턴스가 둘이면 서로 모른다. 코드에도 `TODO ... IMPORTANT!!!` 주석이 있다.
- `POST /{sessionId}/set-document` 도 이 맵에 없으면 404 를 낸다 —
  재시작 후 첫 `set-document` 가 실패하는 원인이 여기다.

### B-4. sessionId 가 매번 같다

- **사양이다.** `UUID.nameUUIDFromBytes(creatorName.getBytes())` — 결정적 해시.
  프론트가 `creatorName` 자리에 **documentId** 를 넣으므로 문서마다 고정 sessionId 가 된다.
- 부작용: 이름이 같으면 서로 다른 사용자가 같은 세션에 들어간다. 랜덤 ID 로 바꾸면
  프론트의 "문서 → 세션" 결정성이 깨지므로 **양쪽을 함께 고쳐야 한다.**

### B-5. 참가자 목록이 비어 있다

- `getActiveParticipantsForDocument` 는 실패·부재 시 전부 **빈 리스트**를 돌려준다(예외 없음).
  키(`session:users:{sid}:{did}`)가 TTL 로 사라졌는지 먼저 확인한다.
- `/app/join` 없이 구독만 하면 등록되지 않는다. 구독 ≠ 참가.

---

## C. 락

### C-1. Middle-Proxy 가 죽었는데 UI 는 "아무도 안 잡음"이라고 나온다 ⚠️

- **원인**: `WikiLockService` 의 모든 메서드가 `catch (Exception)` 후
  `IDLE` 상태 또는 `false` 를 반환한다. 장애가 **정상 상태로 위장**된다.
- 결과적으로 여러 사람이 동시에 "내가 편집 권한 있음"으로 오인할 수 있다.
- **확인**: 로그 `[Lock] Lock API error ...`.

### C-2. 락 TTL·takeover 시간을 바꿔도 반영이 안 된다

- 상수는 이 저장소가 아니라 **Middle-Proxy** `com.arms.api.wiki.service.WikiLockService` 에 있다
  (`LOCK_TTL_SECONDS = 120`, `TAKEOVER_IDLE_MILLIS = 60_000`).

### C-3. 하트비트만 보내는데 락을 뺏긴다

- **의도된 설계다.** 유휴 takeover 창은 `touchActivity`(= `/app/selection` 수신) 로만 리셋된다.
  `/app/lock/heartbeat` 는 TTL 만 연장한다. "실제 타이핑만이 문서를 예약한다"
  (`EditorController` 주석에 명시).

### C-4. `STATE_LOCKED` 상수가 없다고 컴파일 에러

- Broker-Hub `LockState` 에는 `STATE_IDLE` 만 있다. `STATE_LOCKED` · `EVENT_ACQUIRED` 는
  **Middle-Proxy 쪽 DTO 에만** 있다. 두 클래스는 별개다 — `references/lock-delegation.md` 대조표 참조.

---

## D. 기동 · 설정

### D-1. `Could not resolve placeholder 'spring.redis.host'` 로 기동 실패 ⚠️

- **원인**: `RedisConfig` 가 **Boot 3 에서 제거된 구키** `spring.redis.host/port` 를
  `@Value` 로 직접 읽는다(기본값 없음). Boot 3 표준 키는 `spring.data.redis.*` 다.
- `application-dev.yml` 이 **두 키를 모두** 적어 놓은 이유가 이것이다. 한쪽만 지우면 안 뜬다.
- live/stg 로컬 yml 에는 Redis 설정이 아예 없다 → **Config 서버가 반드시 주입해야 한다.**

### D-2. `spring.redis.ssl.enable` 을 켰는데 SSL 이 안 걸린다

- yml 키는 `...ssl.enable`, 코드는 `@Value("${spring.redis.ssl.enabled:false}")`.
  **이름이 다르다.** 기본값 false 라 예외 없이 무시된다. 죽은 설정이다.

### D-3. 웹소켓 연결이 404

- STOMP 엔드포인트는 `/ws` 하나다. 여기에 `/auth-user` 같은 접두를 붙이면 404 가 난다
  (커밋 `95a7b62` 에서 실제로 겪고 되돌린 이력). 접두는 게이트웨이가 붙였다 떼는 몫이다.
- 프론트는 `/auth-user/ws` 로 접속한다 → Middle-Proxy 라우트가 `/ws` 로 리라이트한다.
  라우트는 **Global-Config 주입 yml** 에 있고 이 저장소에도 Middle-Proxy 저장소에도 없다.

### D-4. `httptrace` 액추에이터가 없다

- 세 프로파일 모두 `management.endpoints.web.exposure.include` 에 `httptrace` 가 있으나
  Boot 3 에서 이름이 `httpexchanges` 로 바뀌었다. **죽은 항목**이다(다른 것들은 정상 동작).

### D-5. `mat.*` 설정이 아무 일도 안 한다

- `mat`(MultiAgent Tracker) 소스는 커밋 `ffff1b0` 에서 **제거됐다.** yml 의 `mat.mode` ·
  `mat.remote.*` 와 `build.gradle` 의 `lanterna` 의존성은 **잔재**다. 되살리려 하지 말 것.

---

## E. 빌드

### E-1. `./gradlew build` 가 네트워크에서 멈추거나 실패한다

- `build.gradle` 의 `ext` 블록이 버전 산정을 위해 Nexus 에서 `metadata.xml` 을 `wget` 으로 받는다.
  Windows·Mac 은 스킵하고 동봉된 `metadata.xml` 을 쓰지만 **Linux 는 네트워크가 필요**하다.
- 검증 목적이면 `compileJava` 만 돌린다.

### E-2. Java 버전 혼동

- `README.md` 는 "Java 17" — **틀렸다.** toolchain 21, Dockerfile `openjdk:21-jdk`.
- 코드가 실제로 Java 17+ 문법을 쓴다(`RedisConfig` 의 text block,
  `HighlightingCompositeConverterCustom` 의 switch expression).

### E-3. `sonarqube` 블록에 평문 자격증명이 있다

- `build.gradle` 에 Sonar `login`/`password` 가 평문으로 박혀 있다.
  **값을 다른 파일·로그·문서에 복제하지 않는다.** 정리 제안은 할 수 있으나 요청 없이 건드리지 않는다.

---

## F. 직렬화

### F-1. 히스토리에서 `Unexpected non-string type found in history`

- `RedisTemplate` 의 value serializer 는 `GenericJackson2JsonRedisSerializer` 다.
  히스토리 원소는 "JSON 문자열을 다시 JSON 으로 감싼" 형태로 저장된다.
  다른 클라이언트(redis-cli · 다른 직렬화 설정)가 같은 키에 쓰면 이 경고와 함께 **조용히 건너뛴다**
  → op 유실 → 내용 분기.
- **`RedisTemplate`(JSON)과 `StringRedisTemplate`(문자열)이 같은 키를 공유하지 않게 유지할 것.**
  현재 분리 상태: `doc:*`·`messages`·`health-check` 는 `RedisTemplate`,
  `user:active_docs:*` 는 `StringRedisTemplate`, `session:users:*` 는 `RedisTemplate` 의 Hash.

### F-2. `TextOperation` 의 JSON 은 배열이다

- `@JsonValue getOps()` + `@JsonCreator TextOperation(List<Object>)` 이므로
  `{"ops":[...]}` 가 아니라 **`[3,"abc",-2]`** 형태로 직렬화된다.
  DTO 를 새로 만들 때 이 형태를 깨지 말 것.

### F-3. `setOps()` 는 길이를 재계산하지 않는다

- `TextOperation.setOps` 는 `baseLength`/`targetLength` 를 갱신하지 않는다(코드 주석에 경고 있음).
  **쓰지 말고** `@JsonCreator` 생성자나 `retain/insert/delete` 빌더를 쓴다.

---

## G. 죽은 코드 (건드리기 전에 확인)

요청 없이 지우지 말 것. 다만 "이걸 고치면 될 것 같다" 고 착각하기 쉬운 것들이다.

| 대상 | 상태 |
|------|------|
| `DwrClient` | 어디서도 호출하지 않는다. URL `http://backend-core:31313` 하드코딩 |
| `SlackNotificationService` | 빈은 등록되지만 **주입받아 쓰는 곳이 없다.** stg·live 에서만 동작하도록 가드됨 |
| `DataSerializer` | 참조 0건 |
| `SessionRegistryService.userLeftAllSessions` | 참조 0건. `KEYS *` 스캔이라 운영에서 위험 |
| `OtService.resetSessionDocument` · `getOperationHistory` | 참조 0건 |
| `OtUtils.invert` · `compose` | 참조 0건(구현은 정상) |
| `OtController.handleSelection` | `@Deprecated` + `@MessageMapping` 제거됨 → 매핑 안 됨 |
| `RangeInfo` · `IncomingSelectionPayload` | 참조 0건. `SelectionInfo` 는 필드가 `String message` 하나뿐 |
| `SlackResponse` | 참조 0건 (`SlackMessageDTO` 는 `SlackNotificationService` 가 쓴다) |
| `ThreadPoolConfig.executor` | 빈은 뜨지만 주입처 없음. `@EnableScheduling` 은 주석 처리 |
| `AppConfig.restTemplate` | `CodeExecutionController` 만 쓴다 |
| `WebSocketController` / `WebSocketMessage` | `/app/message` 채널. 프론트에서 쓰는 흔적 없음 |
| `CodeExecutionController` | 외부 `emkc.org` Piston API 프록시. 위키 편집과 무관 |
| `lanterna` 의존성 · `mat.*` yml | 제거된 mat 기능의 잔재 (D-5) |

---

## H. 빠른 진단 명령

```bash
# 문서 상태
redis-cli GET  "doc:{<sessionId>}:content:<documentId>"
redis-cli LLEN "doc:{<sessionId>}:history:<documentId>"     # 500 이면 A-1 의심

# 참가자
redis-cli HGETALL "session:users:<sessionId>:<documentId>"
redis-cli TTL     "session:users:<sessionId>:<documentId>"   # -2 면 이미 만료

# 사용자 추적셋
redis-cli SMEMBERS "user:active_docs:<userId>"

# 락(소유자는 Middle-Proxy)
curl "http://<middle-proxy>:13131/wiki/lock/snapshot?sessionId=<sid>&documentId=<did>"

# 앱
curl http://<broker-hub>:31113/api/health/redis
curl http://<broker-hub>:31113/actuator/health
```

> 키에 `{}` 가 그대로 들어간다. `{sessionId}` 의 중괄호는 Redis Cluster 해시태그이므로
> **실제 키 문자열의 일부**다. 빼고 조회하면 안 나온다.
