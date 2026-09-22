# STOMP 채널 계약

Broker-Hub 의 공개 API 는 REST 가 아니라 **STOMP 목적지 문자열**이다.
서버·클라이언트 어느 한쪽만 바꾸면 **예외 없이 조용히 동작하지 않는다.**

클라이언트 정본: `Java-Service-Tree-Framework-Frontend-Web/arms/js/adms/session-manager.js`

---

## 1. 브로커 설정 (`config/WebSocketConfig`)

```java
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        config.enableSimpleBroker("/topic");                 // 인메모리 브로커
        config.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")
                .withSockJS();
    }
}
```

- **`/user` 접두(사용자 전용 큐)는 설정돼 있지 않다.** 특정 사용자에게만 보내려면
  현재 코드처럼 `/topic/ack/{clientId}` 같은 **식별자를 목적지에 박는** 방식을 쓴다.
- 엔드포인트에 인증 접두(`/auth-user`)를 붙이면 404. 접두는 게이트웨이의 몫이다.
- `Principal` 을 채우는 `HandshakeHandler`·`ChannelInterceptor` 가 **없다**(§6 참조).

---

## 2. 클라이언트 → 서버 전수 목록

### `/app/join` — `EditorController.handleJoin`

```json
{ "sessionId": "...", "documentId": "...", "userId": "...", "userName": "...", "userColor": "#RRGGBB" }
```
DTO: `JoinPayload`. **5개 필드가 전부 non-null 이어야 한다** — 하나라도 null 이면
`log.warn` 후 **아무 응답 없이 종료**(클라이언트는 영원히 기다린다).

처리:
1. `SessionRegistryService.userJoined(sessionId, documentId, UserInfoDTO)` — Redis Hash 등록
2. `SADD user:active_docs:{userId} "{sessionId}:{documentId}"` + TTL 24시간 갱신
3. `broadcastFullDocumentState(...)` → state 토픽
4. `broadcastLockSnapshot(...)` → lock 토픽 (편집자·관람자 모두 현재 점유자를 알게 되는 지점)

### `/app/leave` — `EditorController.handleLeave`

`JoinPayload` 를 그대로 재사용한다(프론트도 join/leave 에 같은 봉투를 쓴다).
`sessionId`·`documentId`·`userId` 3개만 검사한다.
처리: `userLeftDocument` → `SREM` 추적셋 → state 토픽 방송.
**락 해제는 하지 않는다** — 클라이언트가 `/app/lock/release` 를 따로 보내야 한다.

### `/app/selection` — `EditorController.handleSelectionUpdate`

```json
{
  "sessionId": "...", "documentId": "...",
  "userInfo": {
    "id": "...", "name": "...", "color": "#RRGGBB",
    "cursorPosition": { "lineNumber": 1, "column": 1 },
    "selection": { "message": "..." }
  }
}
```
DTO: `CursorMessage` → `UserInfo` → `Position` · `SelectionInfo`.

> ⚠️ `SelectionInfo` 의 필드는 **`String message` 하나뿐**이다. `RangeInfo`(anchor/head)는
> 정의만 있고 어디에도 연결돼 있지 않다. 선택 영역을 구조적으로 다루려면 DTO 확장이 필요하다.

처리:
1. `Position` → `Map<String,Integer>{lineNumber, column}` 으로 변환 후
   `SessionRegistryService.updateUserState` 로 Redis 갱신 (사용자가 없으면 경고만)
2. **`wikiLockService.touchActivity(...)`** — 유휴 takeover 창 리셋 (이 채널에서만 일어난다)
3. `messagingTemplate.convertAndSend(selections 토픽, message)` — **원본 그대로** 방송

### `/app/operation` — `OtController.handleOperation`

```json
{
  "clientId": "...", "sessionId": "...", "documentId": "...",
  "revision": 12,
  "operation": [5, "abc", -2],
  "selection": { },
  "cursorPosition": { "lineNumber": 1, "column": 6 }
}
```
DTO: `IncomingOperationPayload`. `clientId`·`documentId`·`sessionId` 중 하나라도 null 이면 폐기.

처리: `new TextOperation(payload.getOperation())` → `OtService.receiveOperation(...)` →
operations 토픽 방송(+ selection/cursorPosition 이 있으면 함께) → `/topic/ack/{clientId}` 로 `"ack"`.

> ⚠️ 실패 시(`IllegalArgumentException` 또는 일반 예외) **로그만 남고 ACK 도 에러도 안 간다.**
> 클라이언트 입장에서는 "응답 없음"이다. 새 에러 처리를 넣는다면 이 지점이다.

### `/app/get-document-state` — `OtController.getDocumentState`

```json
{ "documentId": "...", "sessionId": "..." }
```
`Map<String,String>` 을 그대로 받는다(전용 DTO 없음).
응답은 요청자 개인이 아니라 **state 토픽으로 브로드캐스트**된다 — 요청자가 그 토픽을 구독하고 있어야 한다.

### `/app/chat` — `ChatController.handleChatMessage`

```json
{ "sessionId": "...", "userId": "...", "userName": "...", "userColor": "...",
  "message": "...", "timestamp": "2026-09-22T10:00:00" }
```
`timestamp` 가 null 이면 서버가 `LocalDateTime.now()` 로 채운다.
응답 JSON 에는 `formattedTimestamp`(`HH:mm`)가 `@JsonProperty` 로 추가된다.
방송 대상: `/topic/sessions/{sessionId}/chat` — **documentId 로 나뉘지 않는다**(세션 단위).

### `/app/message` — `WebSocketController.broadcastMessage`

`WebSocketMessage`(code + user{name,color,cursor{cursorPosition,selection}}).
`RPUSH messages` 후 `@SendTo("/topic/messages")`. **프론트에서 쓰는 흔적이 없다.**

### `/app/lock/**` — `LockController`

4개 채널 모두 `LockCommand` 를 받는다.

```json
{ "sessionId": "...", "documentId": "...", "userId": "...", "userName": "...", "reason": "DONE" }
```

| 목적지 | 필수 필드 | 결과 방송 |
|--------|----------|-----------|
| `/app/lock/acquire` | sessionId, documentId, userId | Middle-Proxy 가 준 `LockState` 그대로 |
| `/app/lock/release` | 〃 (`reason` 없으면 `DONE`) | 성공 → `RELEASED`, 실패 → 현재 스냅샷 |
| `/app/lock/heartbeat` | 〃 | 성공 → 스냅샷 + `event=HEARTBEAT`, 실패 → 스냅샷 |
| `/app/lock/force-release` | 〃 | 성공 → `RELEASED`/`FORCED`, 거부 → 현재 스냅샷 |

> 실패해도 **항상 진실(스냅샷)을 다시 방송한다.** 클라이언트 버튼 상태가 스스로 교정되게 하려는 설계다.

---

## 3. 서버 → 클라이언트 전수 목록

| 토픽 | 페이로드 | 보내는 곳 |
|------|----------|-----------|
| `/topic/sessions/{sid}/state/document/{did}` | `DocumentState` | `EditorController`(join·leave) · `OtController`(get-state) · `WebSocketEventListener`(disconnect) |
| `/topic/sessions/{sid}/operations/document/{did}` | `Map{documentId, clientId, operation, sessionId, selection?, cursorPosition?}` | `OtController` |
| `/topic/sessions/{sid}/selections/document/{did}` | `CursorMessage`(수신 원문) | `EditorController` |
| `/topic/sessions/{sid}/lock/document/{did}` | `LockState` | `LockController` · `EditorController`(join) · `WebSocketEventListener` |
| `/topic/sessions/{sid}/chat` | `ChatMessage` | `ChatController` |
| `/topic/ack/{clientId}` | `"ack"` (문자열) | `OtController` |
| `/topic/messages` | `WebSocketMessage` | `WebSocketController` |

`DocumentState`:
```json
{ "documentId": "...", "document": "전체 내용", "revision": 12,
  "sessionId": "...", "participants": [ UserInfoDTO... ] }
```

`UserInfoDTO`(Redis 저장 타입 = 방송 타입):
```json
{ "id": "...", "name": "...", "color": "...",
  "cursorPosition": { "lineNumber": 1, "column": 1 },
  "selection": { "message": "..." } }
```

> `UserInfo`(수신용, `cursorPosition` 이 `Position` 객체)와 `UserInfoDTO`(저장·방송용,
> `cursorPosition` 이 `Map<String,Integer>`)는 **다른 클래스**다. 변환은
> `EditorController.handleSelectionUpdate` 가 손으로 한다. 합치려 하지 말 것 — 직렬화 형태가 다르다.

---

## 4. 채널을 새로 추가할 때

1. **핸들러**: 해당 도메인 컨트롤러에 `@MessageMapping("/app/...")` 추가. 반환값 없이
   `SimpMessagingTemplate.convertAndSend` 로 방송하는 것이 이 저장소의 지배적 패턴이다
   (`@SendTo` 는 `WebSocketController` 한 곳뿐).
2. **검증**: null 검사 후 `log.warn` + `return`. 예외를 던지지 않는 것이 기존 관례다.
   단, **조용한 실패가 되는지** 판단하고 필요하면 에러 채널을 함께 설계한다.
3. **목적지 문자열**: `/topic/sessions/{sessionId}/<용도>/document/{documentId}` 규약을 따른다.
   세션 단위면 `/topic/sessions/{sessionId}/<용도>`(chat 처럼).
   **상수 또는 static helper 로 뽑는 것을 권장한다** — `WikiLockService.lockDestination()` 이 좋은 예다.
4. **프론트**: `session-manager.js` 에 `_subscribeXxx` / `_unsubscribeXxx` 쌍과 발행 메서드를 추가한다.
5. **재연결**: 프론트는 재연결 시 `_unsubscribeAll()` → `_subscribeAllAndJoin()` 을 한다.
   새 구독을 이 흐름에 반드시 편입시킨다.

---

## 5. REST 엔드포인트

### `POST /api/sessions/create`
```json
요청 { "creatorName": "..." }     // 프론트는 여기에 documentId 를 넣는다
응답 { "sessionId": "..." }       // UUID.nameUUIDFromBytes(creatorName) — 결정적
```
`static ConcurrentHashMap activeSessions` 에 등록한다(재시작 시 소실).

### `GET /api/sessions/{sessionId}` → `SessionInfo{id, creatorName, createdAt}` 또는 404

### `POST /api/sessions/{sessionId}/set-document`
```json
{ "documentId": "...", "content": "초기 내용" }
```
DTO: `DocumentContentPayload`.
- `documentId` 없으면 400, 세션이 맵에 없으면 404.
- `OtService.setDocumentContent` → **content SET + history DELETE** → 리비전이 0 으로 리셋된다.
  접속 중인 클라이언트가 옛 리비전을 들고 있으면 이후 op 가 전부 거부된다(`pitfalls.md` A-2).

### `POST /api/execute` → 외부 `https://emkc.org/api/v2/piston/execute` 프록시
요청 본문 `CodeExecutionRequest{language, version, files[{content}]}` 를 그대로 전달하고
응답 문자열을 그대로 반환한다. 실패 시 `"Error: ..."` 문자열(상태코드는 200).
**위키 편집과 무관한 기능이다.**

### `GET /api/health/redis` → `"Redis connection is OK"` / `"Redis connection failed: ..."`
`health-check` 키에 `"OK"` 를 쓰고 되읽는다(TTL 없음).

---

## 6. 인증 · Principal

- 이 저장소에는 **Spring Security 의존성이 없다.** 모든 엔드포인트가 무방비다.
  보호는 전적으로 Middle-Proxy 게이트웨이(`/auth-user/**` → Keycloak)에 의존한다.
- 따라서 `@MessageMapping` 메서드가 받는 `Principal` 은 **항상 null** 이다.
  - `OtController.getDocumentState` 는 null 이면 경고만 남기고 계속 진행한다(동작에 영향 없음).
  - `WebSocketEventListener` 는 null 이면 **정리를 통째로 건너뛴다**(`pitfalls.md` B-1 — 실질적 버그).
- 사용자 식별은 전부 **페이로드의 `userId` / `clientId`** 로 한다. 신뢰 경계가 게이트웨이임을 전제한 설계다.
- 과거 이 저장소에 권한 처리를 넣었다가 롤백한 이력이 있다(커밋 `d8edd8a` → `ebabc41`).
  다시 넣으려면 그 이력을 먼저 확인할 것.
