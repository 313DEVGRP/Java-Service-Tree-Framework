# 위키 편집락 — Middle-Proxy 위임 계약

**락의 소유자는 이 저장소가 아니다.**
Broker-Hub 는 Feign 으로 Middle-Proxy 에 위임하고, 그 결과를 STOMP 로 방송한다.

락 관련 요청이 들어오면 **가장 먼저 "실제 수정 지점이 어디인가"를 판별**한다.

---

## 1. 책임 분할

| 책임 | 어디 |
|------|------|
| 락 획득·해제·연장·강제회수의 **원자 로직** | **Middle-Proxy** `com.arms.api.wiki.service.WikiLockService` (Redis Lua) |
| 락 정책 상수 (TTL 120초 · 유휴 60초 takeover) | **Middle-Proxy** 같은 파일 |
| 락 상태 **저장** | **Middle-Proxy** `WikiLockRepository` (Redis 키스페이스 `wiki:lock`) |
| 락 명령 수신 (STOMP) | Broker-Hub `LockController` |
| 락 상태 **방송** (STOMP) | Broker-Hub `LockController` · `EditorController` · `WebSocketEventListener` |
| 편집 활동 감지 → 유휴 창 리셋 | Broker-Hub `EditorController.handleSelectionUpdate` |
| 장애 시 폴백 | Broker-Hub `WikiLockService` |

### 판별 기준

| 요청 | 수정 지점 |
|------|-----------|
| "락 유지 시간을 늘려줘" / "몇 분 뒤에 뺏을 수 있게" | **Middle-Proxy** |
| "락 획득 조건을 바꿔줘"(예: 관리자는 항상 뺏기) | **Middle-Proxy** |
| "락 상태를 다른 채널로도 알려줘" | Broker-Hub |
| "락을 잡은 사람 이름이 화면에 안 나와" | 방송 페이로드 → Broker-Hub, 값 자체 → Middle-Proxy |
| "브라우저 닫으면 락이 안 풀려" | **Broker-Hub** (`pitfalls.md` B-1/B-2) |
| "저장했는데 락이 안 풀려" | Broker-Hub → 프론트 `/app/lock/release` 발행 여부부터 확인 |

---

## 2. 호출 경로

```
프론트  session-manager.js  _publishLock("/app/lock/acquire")
   ↓ STOMP
Broker-Hub  LockController.handleAcquire(LockCommand)
   ↓
Broker-Hub  WikiLockService.acquire(...)            ← 얇은 어댑터 + 폴백
   ↓ Feign
Broker-Hub  WikiLockClient  @FeignClient(name="middle-proxy-wiki-lock", url="${arms.middle-proxy.url}")
   ↓ HTTP
Middle-Proxy  WikiLockController  @RequestMapping("/wiki/lock")
   ↓
Middle-Proxy  WikiLockService  →  WikiLockRepository  →  Redis (Lua, 원자적)
```

`arms.middle-proxy.url` 은 **Config 서버가 주입**한다(dev `http://127.0.0.1:13131`,
stg/live `http://middle-proxy:13131`). 이 저장소 yml 에는 없다.

Middle-Proxy 의 `/wiki/lock/**` 는 `SecurityConfiguration` 에서 **permitAll**(내부 호출 전용)이다.

---

## 3. Feign 인터페이스 (`client/middleproxy/WikiLockClient`)

| 메서드 | HTTP | 반환 |
|--------|------|------|
| `acquire(LockRequest)` | `POST /wiki/lock/acquire` | `LockState` |
| `release(LockRequest)` | `POST /wiki/lock/release` | `boolean` |
| `renew(LockRequest)` | `POST /wiki/lock/renew` | `boolean` |
| `touchActivity(LockRequest)` | `POST /wiki/lock/touch` | `boolean` |
| `forceRelease(LockRequest)` | `POST /wiki/lock/force-release` | `boolean` |
| `snapshot(sessionId, documentId)` | `GET /wiki/lock/snapshot` (`@RequestParam`) | `LockState` |

`LockRequest` = `{sessionId, documentId, userId, userName, reason}` (Lombok `@AllArgsConstructor`).

Feign 등록: `config/OpenFeignConfig` — `@EnableFeignClients({"com.arms.client.dwr", "com.arms.client.middleproxy"})`.
디코더: `config/FeignResponseDecoderConfig` 가 `SpringDecoder` 를 등록한다.
HTTP 클라이언트는 `io.github.openfeign:feign-hc5`(Apache HttpClient 5).

> Middle-Proxy 와 달리 이 저장소는 **MVC 라 `HttpMessageConverters` 가 정상 구성된다.**
> 따라서 `@RequestBody` 사용에 문제가 없다(Middle-Proxy 쪽 제약과 혼동하지 말 것).

---

## 4. `WikiLockService` — 폴백 정책 ⚠️

이 저장소의 `WikiLockService` 는 **모든 메서드가 예외를 삼킨다.**

| 메서드 | 실패 시 반환 | 위험 |
|--------|-------------|------|
| `acquire` | `IDLE` + `event=DENIED` + `requesterId` | 상태는 IDLE 인데 이벤트는 DENIED — 클라이언트가 해석을 잘못하기 쉽다 |
| `release` | `false` | 호출자가 스냅샷을 다시 방송 → 그 스냅샷도 실패하면 `IDLE` |
| `renew` | `false` | 하트비트가 조용히 무효화 |
| `touchActivity` | `false` | 유휴 창이 리셋되지 않아 편집 중에 락을 뺏길 수 있다 |
| `forceRelease` | `false` | |
| `snapshot` | `IDLE` + `event=SNAPSHOT` | **가장 위험** — Middle-Proxy 장애가 "아무도 안 잡음"으로 보인다 |

> **Middle-Proxy 가 죽으면 UI 는 모두에게 "편집 가능"으로 보인다.**
> 여러 사람이 동시에 편집에 들어가고 OT 는 그것을 막지 않는다(OT 는 병합할 뿐 배타성을 보장하지 않는다).
> 로그 `[Lock] Lock API error ...` 가 유일한 단서다.
>
> 개선한다면 `UNKNOWN` 상태를 추가해 클라이언트가 "확인 불가"로 표시하게 하는 방향이다.
> **DTO·프론트 동시 변경이므로 사용자 확인을 받고 진행할 것.**

`lockDestination(sessionId, documentId)` 는 이 저장소에서 **유일하게 상수화된 토픽 헬퍼**다.
새 채널을 만들 때 이 형태를 본뜨는 것을 권한다.

```java
private static final String LOCK_TOPIC_FORMAT = "/topic/sessions/%s/lock/document/%s";
public static String lockDestination(String sessionId, String documentId) { ... }
```

---

## 5. `LockState` DTO 대조표 ⚠️

두 저장소에 **같은 이름의 다른 클래스**가 있다. 필드는 같고 **상수 집합이 다르다.**

| 상수 | Broker-Hub | Middle-Proxy |
|------|-----------|--------------|
| `STATE_IDLE` | ✅ | ✅ |
| `STATE_LOCKED` | ❌ **없음** | ✅ |
| `EVENT_ACQUIRED` | ❌ **없음** | ✅ |
| `EVENT_RELEASED` | ✅ | ✅ |
| `EVENT_DENIED` | ✅ | ✅ |
| `EVENT_SNAPSHOT` | ✅ | ✅ |
| `EVENT_HEARTBEAT` | ✅ | ❌ 없음 |
| `REASON_DONE` | ✅ | ❌ 없음 |
| `REASON_DISCONNECT` | ✅ | ❌ 없음 |
| `REASON_FORCED` | ✅ | ❌ 없음 |

필드(양쪽 동일, 순서도 동일):

```
sessionId · documentId · state · holderId · holderName
acquiredAt · lastActivityAt · takeoverIdleMillis · expiresAt · serverTime
event · requesterId · releaseReason
```

시각 필드는 전부 `long`(epoch millis)이다. `serverTime` 을 함께 보내므로
클라이언트는 **자기 시계 대신 서버 시각 기준으로 남은 시간을 계산**할 수 있다.

> 새 상수를 추가할 때는 **반드시 양쪽을 대조**하고, 문자열 리터럴을 코드에 직접 박지 않는다.
> 값이 다르면 JSON 은 통과하지만 클라이언트 분기가 조용히 빗나간다.

---

## 6. Middle-Proxy 쪽 동작 요약 (정본은 해당 저장소)

```java
LOCK_TTL_SECONDS      = 120       // 락 TTL
TAKEOVER_IDLE_MILLIS  = 60_000    // 이 시간 이상 유휴면 강제 회수 허용
```

키: `wiki:lock` 키스페이스 · 서브키 `{sessionId}:{documentId}` · 값은 JSON
`{holderId, holderName, acquiredAt, lastActivityAt}`.

- **acquire**: `setIfAbsent`(SET NX PX). 실패 시 현재 점유자 조회 →
  본인이면 **재진입**(TTL 갱신 후 `ACQUIRED`), 타인이면 `DENIED` + `requesterId` 설정.
  만료 경합 대비로 **최대 2회 재시도**하고, 그래도 확정 못 하면 스냅샷 + `DENIED` 를 돌려준다.
- **release**: `deleteIfFieldEquals(holderId)` — **본인 소유일 때만** 삭제(Lua, 원자적).
- **renew** / **touch**: TTL 연장 / `lastActivityAt` 갱신.
- **force-release**: 유휴 시간이 `TAKEOVER_IDLE_MILLIS` 를 넘었을 때만 허용.

---

## 7. 방송 시점 정리

| 시점 | 보내는 곳 | 페이로드 |
|------|----------|----------|
| `/app/lock/acquire` 처리 후 | `LockController.handleAcquire` | Middle-Proxy 응답 그대로 (`ACQUIRED` 또는 `DENIED`) |
| `/app/lock/release` 성공 | `LockController.handleRelease` | `releasedState(reason)` — `IDLE` + `RELEASED` |
| `/app/lock/release` 실패 | 〃 | `snapshot(...)` (진실 재방송) |
| `/app/lock/heartbeat` 성공 | `LockController.handleHeartbeat` | `snapshot` + `event=HEARTBEAT` |
| `/app/lock/heartbeat` 실패 | 〃 | `snapshot` 그대로 |
| `/app/lock/force-release` 성공 | `LockController.handleForceRelease` | `IDLE` + `RELEASED` + `reason=FORCED` |
| `/app/lock/force-release` 거부 | 〃 | `snapshot` (버튼 상태 자가 교정) |
| `/app/join` | `EditorController.broadcastLockSnapshot` | `snapshot` (`event=SNAPSHOT`) |
| disconnect 시 release 성공 | `WebSocketEventListener.broadcastLockReleased` | `IDLE` + `RELEASED` + `reason=DISCONNECT` |

**거부(`DENIED`)도 전체에게 방송된다.** 요청자 전용 채널이 없기 때문이다.
클라이언트는 `requesterId` 가 자기일 때만 소비해야 한다(프론트 주석에 명시돼 있다).

> `LockController` 는 `@RestController` 로 선언돼 있지만 HTTP 매핑이 하나도 없고
> `@MessageMapping` 만 쓴다. 동작에는 문제가 없으나 **의도는 `@Controller`** 다.
> 다른 STOMP 컨트롤러(`EditorController`·`OtController`·`ChatController`)는 모두 `@Controller` 다.
> 새로 만들 때는 `@Controller` 를 쓴다.

---

## 8. 활동 감지 설계 (의도를 바꾸지 말 것)

```java
// EditorController.handleSelectionUpdate 주석 요약
// 이 채널의 활동이 홀더의 락을 살려 두고 유휴 takeover 창을 리셋한다.
// 실제 타이핑만이 문서를 예약한다 — 하트비트만으로는 안 된다.
// 스크립트가 소유권을 검증하므로 관람자에게는 no-op 이다.
wikiLockService.touchActivity(sessionId, documentId, senderClientId);
```

- `/app/lock/heartbeat` → **TTL 연장만**. 유휴 창은 그대로 흐른다.
- `/app/selection` → **유휴 창 리셋**.

"자리 비운 사람에게서 문서를 회수한다"는 정책의 핵심이다.
하트비트에 `touchActivity` 를 추가하면 **정책 자체가 무너진다.** 요청받더라도 이 영향을 먼저 설명할 것.
