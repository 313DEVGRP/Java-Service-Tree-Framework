# Redis 데이터 모델 · 세션 생명주기

Broker-Hub 의 영속 계층은 Redis 뿐이다. RDB·JPA·MyBatis 는 없다.

---

## 1. 접속 설정 (`config/RedisConfig`)

```java
@Value("${spring.redis.host}")              // Boot 3 표준은 spring.data.redis.host
@Value("${spring.redis.port}")
@Value("${spring.redis.ssl.enabled:false}")
```

> ⚠️ **Boot 3 에서 제거된 구키를 직접 읽는다.** host/port 는 기본값이 없으므로
> 주입되지 않으면 **컨텍스트 생성 단계에서 기동 실패**한다.
> `application-dev.yml` 이 `spring.data.redis.*` 와 `spring.redis.*` 를 둘 다 적어 놓은 이유가 이것이고,
> live/stg 는 로컬 yml 에 없으니 **Config 서버가 반드시 주입**해야 한다.
>
> dev yml 의 키는 `spring.redis.ssl.enable` 인데 코드는 `...ssl.enabled` 를 읽는다 —
> 이름이 어긋난 **죽은 설정**이다(기본값 false 라 조용히 넘어간다).

구성:
- `LettuceConnectionFactory` — `RedisStandaloneConfiguration` (**Cluster·Sentinel 아님**).
  SSL 은 `useSsl()` 로만 분기. 비밀번호(AUTH) 코드는 주석 처리돼 있다.
- `@PostConstruct logRedisConfig()` 가 host/port/ssl 을 INFO 로 찍는다 — 기동 로그로 즉시 확인 가능.

### 두 개의 템플릿 — 경계를 유지할 것

| 빈 | key / hashKey | value / hashValue | 쓰는 키 |
|----|---------------|-------------------|---------|
| `RedisTemplate<String,Object>` | `StringRedisSerializer` | `GenericJackson2JsonRedisSerializer` | `doc:*`, `session:users:*`, `messages`, `health-check` |
| `StringRedisTemplate` | String | String | `user:active_docs:*` |

**같은 키를 두 템플릿으로 건드리면 깨진다.** 현재는 위와 같이 분리돼 있으니 그 경계를 지킨다.

---

## 2. 키 전수 목록

### `doc:{sessionId}:content:{documentId}` — String, TTL 없음

문서의 현재 전체 내용. `OtService` 만 쓴다.
`{}` 는 Redis Cluster 해시태그 — **실제 키 문자열의 일부**다(redis-cli 조회 시 포함해야 한다).

### `doc:{sessionId}:history:{documentId}` — List, TTL 없음

op JSON 문자열의 append-only 리스트. **최대 500**(Lua 가 `LTRIM`).
길이가 곧 서버 리비전이다 — 이 설계의 결함은 `ot-engine.md` §5 참조.

> **두 키 모두 TTL 이 없다.** 세션이 끝나도 남고, 현재 정리 주체가 없다.
> 문서 수가 늘면 메모리가 단조 증가한다. 정리 기능을 추가한다면
> `resetSessionDocument`(이미 구현돼 있으나 미사용)를 활용할 수 있다.

### `session:users:{sessionId}:{documentId}` — Hash, **TTL 60분**

`userId` → `UserInfoDTO`(JSON). `SessionRegistryService` 가 관리한다.

```
HSET session:users:S1:D1  user42  {"id":"user42","name":"홍길동","color":"#f00",
                                   "cursorPosition":{"lineNumber":3,"column":7},
                                   "selection":{"message":"..."}}
```

TTL 은 **활동이 있을 때마다 갱신**된다(`touchKey`) — join · updateUserState ·
getActiveParticipants(조회만 해도 갱신) · 마지막 사용자가 아닌 leave.
Hash 가 비면 키 자체를 `DEL` 한다.

### `user:active_docs:{userId}` — Set, **TTL 24시간**

원소 형식: `"{sessionId}:{documentId}"`.
`EditorController` 가 join 시 `SADD` + `EXPIRE`, leave 시 `SREM`.
`WebSocketEventListener` 가 disconnect 시 읽어서 정리 대상 목록으로 쓰고 마지막에 `DEL`.

> 원소를 파싱할 때 `docEntry.split(":", 2)` 를 쓴다 — **documentId 에 `:` 가 들어가도 안전**하지만
> **sessionId 에 `:` 가 들어가면 깨진다.** 현재 sessionId 는 UUID 라 문제없다.

### `messages` — List, TTL 없음

`WebSocketController` 가 `RPUSH`. 읽는 곳이 없고 **무한히 자란다.** 사실상 죽은 기능.

### `health-check` — String, TTL 없음

`RedisHealthCheckController` 가 `"OK"` 를 쓰고 되읽는다.

---

## 3. `SessionRegistryService` API

| 메서드 | 동작 | 예외 정책 |
|--------|------|-----------|
| `userJoined(sid, did, UserInfoDTO)` | `HSET` + TTL 갱신 | Redis 실패 시 `logger.severe` 만 (반환값 없음) |
| `userLeftDocument(sid, did, userId)` | `HDEL`, 비면 키 `DEL`, 아니면 TTL 갱신 | 실패 시 `false` |
| `updateUserState(sid, did, userId, cursorMap, selection)` | `HGET` → 필드 갱신 → `HSET` + TTL 갱신 | 사용자 없으면 경고만 |
| `getActiveParticipantsForDocument(sid, did, requestingUserId)` | `HGETALL` → `requestingUserId` 제외 리스트 | 실패·부재 시 **빈 리스트** |
| `userLeftAllSessions(userId)` | `KEYS session:users:*` 전수 스캔 | **미사용. 운영에서 쓰지 말 것** |

> - `updateUserState` 는 read-modify-write 라 **원자적이지 않다.** 같은 사용자의 커서 갱신이
>   동시에 들어오면 하나가 덮인다. 커서는 소실돼도 다음 이벤트로 복구되므로 현재는 허용 가능한 수준이다.
> - `getActiveParticipantsForDocument` 는 **호출처가 전부 `requestingUserId = null`** 로 넘긴다.
>   즉 제외 기능은 구현돼 있지만 실제로는 항상 전원을 반환한다. 필터링은 클라이언트 몫이다.
> - `userLeftAllSessions` 는 `KEYS` 명령을 쓴다 — 운영 Redis 를 멈출 수 있다. **되살리지 말 것.**

---

## 4. 세션 생명주기

### 4.1 정상 흐름

```
① 프론트: POST /auth-user/hub/api/sessions/create   { creatorName: documentId }
       → sessionId (documentId 의 결정적 UUID)
② 프론트: SockJS 연결 /auth-user/ws  → STOMP CONNECT
③ 프론트: 토픽 3종 구독 (state · selections · lock)
④ 프론트: SEND /app/join
       서버: HSET session:users → SADD user:active_docs
             → state 토픽 방송 (participants 포함)
             → lock 토픽 방송 (현재 점유자 스냅샷)
⑤ (선택) POST .../set-document  로 초기 내용 주입 → 리비전 0
⑥ 편집 중: /app/operation · /app/selection · /app/lock/heartbeat
⑦ 종료:   /app/lock/release → /app/leave
```

### 4.2 이탈 경로 3가지

| 경로 | 트리거 | 정리 범위 | 락 해제 |
|------|--------|-----------|---------|
| 명시 이탈 | `/app/leave` | 해당 문서만 (`HDEL` + `SREM`) | **안 한다** — 클라이언트가 따로 보내야 함 |
| 연결 종료 | `SessionDisconnectEvent` | 추적셋의 **모든 문서** + 추적셋 `DEL` | 한다 (`REASON_DISCONNECT`) |
| 방치 | `session:users:*` TTL 60분 | 해당 문서 | 안 함 (Middle-Proxy TTL 120초로 별도 만료) |

### 4.3 `WebSocketEventListener` ⚠️ 현재 동작하지 않는다

```java
Principal userPrincipal = SimpMessageHeaderAccessor.getUser(headers);
if (userPrincipal != null) { /* 정리 */ }
else { log.warn("...No user principal found..."); }   // ← 현재 항상 여기
```

이 저장소에는 Spring Security 도, `Principal` 을 채우는 `HandshakeHandler` ·
`ChannelInterceptor` 도 없다. 따라서 **disconnect 정리 블록 전체가 실질적으로 죽은 코드**다.
증상: 브라우저 강제 종료 시 참가자 목록에 남고 락도 TTL(120초)까지 유지된다.

정리 블록의 설계 자체는 옳다 — 참고용으로 구조를 남긴다:

```
activeDocuments = SMEMBERS user:active_docs:{userId}
for each "sessionId:documentId":
    try { userLeftDocument(...) ; 성공 시 state 토픽 방송 }         ← try 블록 A
    try { wikiLockService.release(..., REASON_DISCONNECT)            ← try 블록 B (분리돼 있음)
          성공 시 lock 토픽 방송 }
DEL user:active_docs:{userId}
```

> try 블록을 **일부러 둘로 나눴다**(코드 주석에 명시). 레지스트리 정리가 실패해도 락은 회수되고,
> 반대도 마찬가지다. 이 구조를 합치지 말 것.

### 4.4 고칠 때의 설계 방향 (확정 전 사용자 확인 필수)

게이트웨이가 전달하는 사용자 식별자를 Principal 로 바인딩해야 한다. 선택지:

1. `DefaultHandshakeHandler.determineUser(...)` 를 오버라이드해 핸드셰이크 요청의
   헤더·쿼리스트링에서 사용자 ID 를 읽는다.
2. `ChannelInterceptor` 로 STOMP `CONNECT` 프레임의 커스텀 헤더를 읽어
   `StompHeaderAccessor.setUser(...)` 한다.

어느 쪽이든 **Middle-Proxy 가 그 값을 실제로 전달하는지** 먼저 확인해야 한다
(현재 게이트웨이 라우트 정의는 Global-Config 에 있고 이 저장소에서 확인 불가).
과거 이 저장소에 권한 처리를 넣었다가 롤백한 이력이 있다(커밋 `d8edd8a` → `ebabc41`).

대안(더 작은 변경): 프론트가 `beforeunload` 에서 `/app/leave` + `/app/lock/release` 를
보내도록 보강한다. 네트워크 단절에는 무력하지만 TTL 이 보호막이 된다.

---

## 5. 새 Redis 키를 추가할 때 체크리스트

- [ ] **TTL 을 정했는가?** 무기한 보관이 필요하면 정리 주체를 명시한다.
- [ ] **어떤 템플릿으로 접근하는가?** `RedisTemplate`(JSON) / `StringRedisTemplate`(문자열).
      기존 키와 섞이지 않게 한다.
- [ ] **멀티키 원자 연산이 필요한가?** 필요하면 키를 `{공통태그}` 로 묶고 Lua 스크립트를
      `RedisConfig` 에 `RedisScript` 빈으로 등록한다(기존 `updateContentAndHistoryScript` 가 예시).
- [ ] **`KEYS` 를 쓰지 않았는가?** 스캔이 필요하면 설계를 다시 본다.
- [ ] **실패 시 정책이 명확한가?** 이 저장소의 관례는 "예외를 삼키고 로그 + 안전한 기본값"이다.
      그 기본값이 **조용한 오동작**을 만들지 않는지 판단한다(락 폴백이 그 반례다).

---

## 6. 진단 명령

```bash
# 문서
redis-cli GET  "doc:{<sessionId>}:content:<documentId>"
redis-cli LLEN "doc:{<sessionId>}:history:<documentId>"
redis-cli LRANGE "doc:{<sessionId>}:history:<documentId>" -3 -1

# 참가자
redis-cli HKEYS   "session:users:<sessionId>:<documentId>"
redis-cli HGETALL "session:users:<sessionId>:<documentId>"
redis-cli TTL     "session:users:<sessionId>:<documentId>"

# 사용자 추적셋
redis-cli SMEMBERS "user:active_docs:<userId>"
redis-cli TTL      "user:active_docs:<userId>"

# 남은 문서 키 개수 (운영에서는 SCAN 권장)
redis-cli --scan --pattern 'doc:*' | wc -l
```

중괄호를 빼면 조회되지 않는다 — 해시태그는 키의 일부다.
