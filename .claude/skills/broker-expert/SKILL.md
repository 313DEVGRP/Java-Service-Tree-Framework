---
name: broker-expert
description: >-
  A-RMS 실시간 협업 브로커 저장소(Java-Service-Tree-Framework-Broker-Hub)의 작업 규약.
  Spring Boot 3.5.6 · Java 21 · Spring Cloud 2025.0.1 기반이며 Backend-Core(Boot 2.6 · Java 11 · JPA) ·
  Middle-Proxy(Boot 2.6 · WebFlux)와 스택도 규칙도 전혀 다르다.
  STOMP/SockJS 웹소켓 채널 · OT(Operational Transformation) 동시편집 엔진 ·
  Redis 문서 상태/히스토리/참가자 레지스트리 · 위키 편집락 방송(Middle-Proxy 위임) ·
  세션 생명주기(join · leave · disconnect) · 채팅 · 코드실행 프록시를 건드릴 때 반드시 먼저 읽을 것.
  WebSocketConfig · enableSimpleBroker · registerStompEndpoints · withSockJS · @MessageMapping ·
  SimpMessagingTemplate · /app/join · /app/operation · /app/selection · /app/lock/acquire ·
  /topic/sessions/{sessionId}/state/document/{documentId} · OtService · OtUtils · TextOperation ·
  retain/insert/delete · revision · updateContentAndHistoryScript · doc:{sessionId}:content ·
  session:users · user:active_docs · SessionRegistryService · WebSocketEventListener ·
  SessionDisconnectEvent · WikiLockClient · LockState · LockCommand · SlackNotificationService ·
  동시편집이 깨짐 · 참가자 목록이 안 지워짐 · 락이 안 풀림 · 웹소켓 404 같은 주제도 대상이다.
  "브로커 허브", "broker hub", "브로커허브", "실시간 협업", "동시편집", "위키 편집", "STOMP", "웹소켓" 요청도 여기서 시작한다.
  단, 같은 "위키 락" 이라도 락의 획득·해제·TTL·takeover 같은 **정책과 원자 로직**은 Middle-Proxy 소유이므로
  middleproxy-expert 다. 여기는 그 락을 STOMP 로 방송하고 편집 활동을 감지하는 쪽이다 —
  "브라우저를 닫았는데 락이 안 풀린다" · "락 상태가 화면에 안 뜬다" 는 여기서 시작한다.
  javax.* · WebSecurityConfigurerAdapter · JPA · WebFlux(Mono/Flux)로 작성하지 않는다 —
  이 저장소는 Boot 3 / Java 21 / MVC + STOMP 이고 영속은 Redis 뿐이다.
---

# A-RMS Broker-Hub 작업 규약

대상 저장소: `Java-Service-Tree-Framework-Broker-Hub/`
(워크스페이스 루트 `C:\DEV\Project\Java-Service-Tree-Framework` 하위, 중첩 git 저장소 · 브랜치 `dev`)

이 저장소는 **A-RMS 위키 문서의 실시간 동시편집을 담당하는 STOMP 브로커**다.
전체가 Java 약 3,900줄 · 47개 파일로 작고, **문서도 테스트도 없다.** 코드가 유일한 정본이다.

작은 대신 계약이 촘촘하다 — 목적지 문자열 하나, Redis 키 하나, 리비전 숫자 하나가 어긋나면
**예외 없이 조용히 틀어진다.** 아래 계약을 먼저 파악하는 것이 이 저장소에서 가장 비용이 싼 길이다.

---

## 0. 30초 요약 — 반드시 먼저 각인할 것

| 항목 | 값 |
|------|----|
| 스택 | Spring Boot **3.5.6** · Spring Cloud **2025.0.1** · **Java 21**(toolchain) · Gradle 8.13 |
| 네임스페이스 | **`jakarta.*`** (워크스페이스에서 Engine-Fire 와 이 저장소만 Boot 3) |
| 웹 모델 | Spring **MVC** + **STOMP over SockJS** (`spring-boot-starter-websocket`) |
| 메시지 브로커 | **`enableSimpleBroker("/topic")`** — 인메모리. 외부 브로커 릴레이 없음 |
| 영속 | **Redis 전용**(Lettuce). RDB · JPA · MyBatis 없음 |
| 인증 | **없음.** Spring Security 의존성 자체가 없다 — 게이트웨이 뒤 내부 전용 |
| 애플리케이션명 | `javaServiceTreeFrameworkBrokerHub` |
| 포트 | **31113** (Global-Config `arms.broker-hub.url` 기준 추정 — `server.port` 는 Config 서버가 주입) |
| 설정 | 저장소 yml 은 뼈대뿐. 대부분 **Spring Cloud Config(Global-Config)가 주입** |
| 배포 | Docker(`313.co.kr:5550/313devgrp/openjdk:21-jdk`) + Nexus + Spinnaker |
| 테스트 | **없음** (`src/test` 디렉토리 자체가 없다) |

> ⚠️ 루트 `README.md` 는 "Java 17" 이라 적혀 있으나 **틀렸다.** `build.gradle` 의 toolchain 은 21,
> Dockerfile 베이스도 `openjdk:21-jdk` 다. 버전 사실은 언제나 `build.gradle` 이 정본이다.

### 이 저장소에서 쓰면 안 되는 것

```
✗ javax.annotation / javax.servlet         → ✓ jakarta.*
✗ WebSecurityConfigurerAdapter / 보안 설정  → ✓ 없음. 인증은 게이트웨이(Middle-Proxy) 책임
✗ @Transactional / JPA Entity              → ✓ RedisTemplate / StringRedisTemplate
✗ Mono / Flux                              → ✓ 값 직접 반환 (이 저장소는 MVC다)
✗ 편집락 로직 직접 구현                     → ✓ WikiLockClient 로 Middle-Proxy 위임 (§5)
✗ 인스턴스 로컬 상태에 의존하는 신규 코드    → ✓ Redis (현재 코드가 이미 위반 중 — §7)
```

---

## 1. 이 서비스가 전체 흐름에서 어디에 있는가

```
브라우저(위키 편집 화면)
  │  arms/js/adms/session-manager.js   ← 클라이언트 정본
  │
  ├─ SockJS  /auth-user/ws ────────────┐
  └─ AJAX    /auth-user/hub/api/... ───┤
                                       ▼
                        Middle-Proxy :13131 (게이트웨이 · Keycloak 인증)
                                       │  라우트는 Global-Config 주입 yml 에 정의
                                       ▼
                        ┌──────── Broker-Hub :31113 ────────┐
                        │  /ws        STOMP 엔드포인트       │
                        │  /api/**    REST                   │
                        │                                    │
                        │  OT 엔진 · 참가자 레지스트리        │
                        └──────┬──────────────────┬──────────┘
                               │                  │
                       Redis(문서·참가자)   Feign → Middle-Proxy /wiki/lock/**
                                                  (편집락의 실제 소유자)
```

**핵심 비대칭 두 가지를 먼저 이해할 것.**

1. **문서 내용·참가자는 Broker-Hub 가 직접 Redis 에 쓴다.**
2. **편집락은 Broker-Hub 가 소유하지 않는다.** Middle-Proxy 가 Redis Lua 로 소유하고,
   Broker-Hub 는 그 결과를 STOMP 로 **방송만** 한다. 락을 고치라는 요청이 오면
   대부분 실제 수정 지점은 이 저장소가 아니다(§5).

---

## 2. STOMP 채널 계약 — 이 저장소의 공개 API

`WebSocketConfig`:
- 애플리케이션 목적지 접두 `/app`
- 브로커 목적지 접두 `/topic` (SimpleBroker, 인메모리)
- 엔드포인트 `/ws` + `setAllowedOriginPatterns("*")` + `withSockJS()`

> ⚠️ 엔드포인트에 `/auth-user` 접두를 붙이면 **404 가 난다**(커밋 95a7b62 에서 되돌린 이력).
> 접두는 게이트웨이가 붙였다 떼는 것이다. 이 저장소는 `/ws` 그대로 유지한다.

### 2.1 클라이언트 → 서버 (`@MessageMapping`)

| 목적지 | 핸들러 | 페이로드 | 하는 일 |
|--------|--------|----------|---------|
| `/app/join` | `EditorController` | `JoinPayload` | 참가자 등록 → 전체 상태 + 락 스냅샷 방송 |
| `/app/leave` | `EditorController` | `JoinPayload` | 참가자 제거 → 전체 상태 방송 |
| `/app/selection` | `EditorController` | `CursorMessage` | 커서/선택 저장 + 방송 + **락 활동 갱신** |
| `/app/operation` | `OtController` | `IncomingOperationPayload` | OT 변환·적용·방송 + 발신자 ACK |
| `/app/get-document-state` | `OtController` | `Map{documentId, sessionId}` | 현재 내용·리비전·참가자 회신 |
| `/app/chat` | `ChatController` | `ChatMessage` | 세션 채팅 방송 |
| `/app/message` | `WebSocketController` | `WebSocketMessage` | Redis `messages` 리스트 적재 + `/topic/messages` |
| `/app/lock/acquire` | `LockController` | `LockCommand` | 락 획득 위임 → 상태 방송 |
| `/app/lock/release` | `LockController` | `LockCommand` | 락 해제 위임 → 상태 방송 |
| `/app/lock/heartbeat` | `LockController` | `LockCommand` | TTL 연장 → 상태 방송 |
| `/app/lock/force-release` | `LockController` | `LockCommand` | 유휴 점유 강제 회수 → 상태 방송 |

### 2.2 서버 → 클라이언트 (토픽)

```
/topic/sessions/{sessionId}/state/document/{documentId}        DocumentState (내용·리비전·참가자)
/topic/sessions/{sessionId}/operations/document/{documentId}   변환된 op 브로드캐스트
/topic/sessions/{sessionId}/selections/document/{documentId}   CursorMessage 원문 그대로
/topic/sessions/{sessionId}/lock/document/{documentId}         LockState
/topic/sessions/{sessionId}/chat                               ChatMessage
/topic/ack/{clientId}                                          "ack" 문자열 (op 수신 확인)
/topic/messages                                                WebSocketMessage (범용, 사실상 미사용)
```

> **토픽 문자열은 세 곳에 흩어져 있다** — `EditorController` · `OtController` ·
> `WebSocketEventListener` 의 `String.format`. 락만 `WikiLockService.lockDestination()` 으로
> 상수화돼 있다. 채널을 바꾸면 **전부** 고치고 프론트 `session-manager.js` 도 함께 고친다.

### 2.3 REST

| 메서드 | 경로 | 컨트롤러 | 비고 |
|--------|------|----------|------|
| POST | `/api/sessions/create` | `SessionController` | `sessionId = UUID.nameUUIDFromBytes(creatorName)` — **결정적** |
| GET | `/api/sessions/{sessionId}` | `SessionController` | **static 인메모리 맵** 조회 |
| POST | `/api/sessions/{sessionId}/set-document` | `SessionController` | 초기 내용 주입 + 히스토리 삭제(리비전 0) |
| POST | `/api/execute` | `CodeExecutionController` | 외부 Piston API(`emkc.org`) 프록시 |
| GET | `/api/health/redis` | `RedisHealthCheckController` | Redis 왕복 확인 |

> 프론트는 `creatorName` 에 **documentId 를 넣어서** 호출한다(`session-manager.js`).
> 즉 같은 문서는 항상 같은 sessionId 로 결정된다. 세션 생성 API 지만 실제로는 **문서 키 해시**다.

상세: `references/stomp-contract.md`

---

## 3. OT 엔진 — 이 저장소의 심장

`ot.js` 를 Java 로 포팅한 것이다. `TextOperation` 은 op 를 **한 리스트에 3종으로 섞어** 표현한다.

```
양수 Integer  → retain(n)     n글자 건너뛰기
String        → insert(str)   삽입
음수 Integer  → delete(-n)    n글자 삭제
```

`baseLength`(적용 전 문서 길이) / `targetLength`(적용 후 길이)가 불변식이다.
`OtUtils.transform(a, b)` 는 **두 op 의 baseLength 가 같을 것**을 요구하고 `[a', b']` 를 돌려준다.

### 3.1 리비전 모델 — 반드시 이해할 것

```
서버 리비전 = Redis 히스토리 리스트의 길이 (LLEN)
```

`/app/operation` 처리 순서(`OtService.receiveOperation`):

```
1. serviceLock.lock()                          ← 인스턴스 로컬 ReentrantLock
2. currentContent = GET  doc:{sid}:content:{did}
   serverRevision = LLEN doc:{sid}:history:{did}
3. clientRevision 검증  (0 <= clientRevision <= serverRevision)
4. clientRevision < serverRevision 이면
       LRANGE history clientRevision .. serverRevision-1  → 동시 op 들
       각각에 대해 transform → transformedOp 갱신
5. newContent = OtUtils.apply(currentContent, transformedOp)
6. Lua 스크립트 원자 실행:  SET content, RPUSH history, LTRIM(최대 500)
7. 변환된 op 를 토픽 방송 + 발신자에게 /topic/ack/{clientId}
```

### 3.2 반드시 알아야 할 결함

> ⚠️ **히스토리 500 트림이 리비전 모델을 깨뜨린다.**
> `MAX_HISTORY_SIZE_PER_DOC = 500` 이고 Lua 가 `LTRIM` 으로 앞을 잘라낸다.
> 그런데 리비전은 `LLEN` 이므로 **히스토리가 500 에 도달한 뒤로는 서버 리비전이 500 에서 멈춘다.**
> 동시에 `LRANGE clientRevision .. serverRevision-1` 의 인덱스는 트림으로 **의미가 어긋난다**
> (인덱스 0 이 더 이상 리비전 0 이 아니다). 결과: 장시간 편집한 문서에서 잘못된 op 로 변환되어
> **사용자마다 내용이 갈라진다.** 예외는 나지 않는다.
>
> 증상("오래 편집하면 화면이 틀어진다")이 보고되면 먼저 여기를 의심한다.
> 고칠 때는 리비전을 별도 카운터(`INCR`)로 분리하고 히스토리 인덱스를 오프셋 보정해야 한다 —
> LTRIM 만 끄는 것은 메모리 증가로 이어지므로 설계 판단이 필요하다. 사용자에게 보고할 것.

상세: `references/ot-engine.md`

---

## 4. Redis 키 지도

| 키 | 타입 | TTL | 쓰는 곳 | 용도 |
|----|------|-----|---------|------|
| `doc:{sessionId}:content:{documentId}` | String | 없음 | `OtService` | 문서 현재 내용 |
| `doc:{sessionId}:history:{documentId}` | List | 없음 | `OtService` | op JSON 히스토리(최대 500) |
| `session:users:{sessionId}:{documentId}` | Hash | **60분** | `SessionRegistryService` | `userId → UserInfoDTO` |
| `user:active_docs:{userId}` | Set | **24시간** | `EditorController` · `WebSocketEventListener` | `"{sessionId}:{documentId}"` 목록 |
| `messages` | List | 없음 | `WebSocketController` | 범용 메시지(사실상 미사용) |
| `health-check` | String | 없음 | `RedisHealthCheckController` | 헬스체크 흔적 |

- `doc:{...}` 키가 **`{sessionId}` 를 해시태그로** 감싼 이유: Redis Cluster 에서 content 와 history 가
  같은 슬롯에 놓여야 Lua 멀티키 스크립트가 돈다. 키 포맷을 바꿀 때 이 제약을 깨지 말 것.
- **문서 내용에는 TTL 이 없다.** 세션이 끝나도 Redis 에 남는다. 정리 주체는 현재 없다.
- 직렬화: `RedisTemplate<String,Object>` 는 key/hashKey `StringRedisSerializer`,
  value/hashValue `GenericJackson2JsonRedisSerializer`. `StringRedisTemplate` 은 순수 문자열.
  **두 템플릿이 같은 키를 건드리면 깨진다** — 현재는 용도가 분리돼 있으니 그 경계를 유지할 것.

상세: `references/redis-and-state.md`

---

## 5. 편집락 — 소유자는 Middle-Proxy 다

이 저장소의 `WikiLockService` 는 **이름과 달리 락을 구현하지 않는다.** Feign 어댑터 + 실패 폴백이다.

```
LockController (@MessageMapping /app/lock/**)
    → com.arms.api.wiki.service.WikiLockService      ← 얇은 위임 계층
        → WikiLockClient (Feign, ${arms.middle-proxy.url})
            → Middle-Proxy  POST /wiki/lock/{acquire,release,renew,touch,force-release}
                            GET  /wiki/lock/snapshot
                → Redis (Lua, 원자적)   ← 락의 진짜 주인
```

정책 상수는 **Middle-Proxy `WikiLockService`** 에 있다: TTL **120초**, 유휴 **60초** 후 takeover 허용.
이 값을 바꾸라는 요청은 이 저장소가 아니라 Middle-Proxy 변경이다.

### 5.1 이 저장소가 실제로 책임지는 것

- **방송**: 모든 락 명령 결과를 `/topic/sessions/{sid}/lock/document/{did}` 로 내보낸다.
  거부(`DENIED`)도 같은 토픽으로 나가고 클라이언트가 `requesterId` 로 자기 것만 소비한다.
- **활동 연장**: `/app/selection` 수신 시 `touchActivity` 호출 — **실제 타이핑만이 문서를 예약한다.**
  하트비트만으로는 유휴 takeover 창이 리셋되지 않는다(의도된 설계).
- **join 시 스냅샷**: 문서를 여는 모든 사람(편집자·관람자)이 별도 채널 없이 현재 점유자를 알게 된다.
- **연결 종료 시 회수**: `WebSocketEventListener` 가 `REASON_DISCONNECT` 로 release + 방송.
- **폴백**: Feign 이 실패하면 예외를 밖으로 던지지 않고 `IDLE` 상태를 반환한다.
  ⚠️ 즉 **Middle-Proxy 가 죽으면 UI 상 "아무도 안 잡고 있음"으로 보인다.** 조용한 실패다.

### 5.2 상태 상수 불일치 (주의)

Broker-Hub `LockState` 에는 `STATE_LOCKED` · `EVENT_ACQUIRED` 상수가 **없다**(Middle-Proxy 에만 있음).
대신 Broker-Hub 에만 `EVENT_HEARTBEAT` · `REASON_DONE/DISCONNECT/FORCED` 가 있다.
필드는 동일하므로 JSON 역직렬화는 성공하지만, **두 DTO 는 별개 클래스이고 상수 집합이 다르다.**
문자열 리터럴을 새로 만들지 말고 반드시 양쪽을 대조한 뒤 상수를 추가한다.

상세: `references/lock-delegation.md`

---

## 6. 세션 생명주기 — 참가자가 사라지는 경로

```
정상 이탈:   /app/leave        → userLeftDocument + 추적셋에서 제거 + 상태 방송
비정상 종료: SessionDisconnectEvent → user:active_docs:{userId} 를 읽어 모든 문서에서 제거
                                     + 각 문서 락 release + 상태/락 방송 + 추적셋 삭제
방치:        session:users:{...} 키 TTL 60분 만료
```

> ⚠️ **disconnect 정리 경로는 `Principal` 에 전적으로 의존한다.**
> `WebSocketEventListener` 는 `SimpMessageHeaderAccessor.getUser(headers)` 가 null 이면
> 경고 로그만 남기고 **아무것도 정리하지 않는다.**
> 그런데 이 저장소에는 Spring Security 도, `Principal` 을 채워 넣는 `HandshakeHandler` 나
> `ChannelInterceptor` 도 **없다.** 따라서 현재 구성에서 이 경로는 사실상 죽은 코드이고,
> 정리는 오직 `/app/leave` 와 TTL 만료에만 의존한다.
> "브라우저를 강제로 닫으면 참가자 목록에 계속 남는다 / 락이 안 풀린다" 는 증상의 원인이 이것이다.
> 고치려면 Principal 을 주입하는 설계가 필요하다(게이트웨이가 전달하는 사용자 식별자를
> 핸드셰이크/CONNECT 헤더에서 읽어 `DefaultHandshakeHandler` 또는 인터셉터로 바인딩).
> **추측으로 고치지 말고 사용자에게 설계 판단을 확인할 것.**

상세: `references/redis-and-state.md` §생명주기

---

## 7. 단일 인스턴스 전제 — 수평 확장 금지

이 서비스는 **2대 이상 띄우면 동작이 깨진다.** 세 가지 이유가 겹쳐 있다.

| 지점 | 문제 |
|------|------|
| `enableSimpleBroker("/topic")` | 인메모리 브로커. A 인스턴스의 방송이 B 의 구독자에게 안 간다 |
| `OtService.serviceLock`(`ReentrantLock`) | 인스턴스 로컬. 두 인스턴스가 동시에 같은 문서를 변환 → 내용 파손 |
| `SessionController.activeSessions` | `static ConcurrentHashMap`. 재시작·다른 인스턴스에서 세션 조회 404 |

Redis 키 설계(해시태그)와 Lua 원자 갱신은 클러스터를 염두에 둔 흔적이지만, **위 3가지가 남아 있는 한
단일 인스턴스가 전제**다. 확장이 필요하면 외부 브로커 릴레이(RabbitMQ/ActiveMQ STOMP) +
분산 락 + 세션 저장소 외부화가 함께 필요하다 — 코드 몇 줄 수정이 아니라 설계 변경임을 보고한다.

---

## 8. 설정 — 대부분 이 저장소에 없다

로컬 yml 에 있는 것은 사실상 이것뿐이다.

| 프로파일 | 내용 |
|----------|------|
| `application.yml` | `spring.application.name` 한 줄 |
| `application-dev.yml` | Config 서버(`www.313.co.kr:33133`), Redis `www.313.co.kr:36379`, actuator, `mat.*` |
| `application-stg/live.yml` | Config 서버(`global-config:33133`), actuator, `mat.*` |

Config 서버가 주입해야 하는 것: **`server.port`**, **live/stg 의 Redis 접속**,
**`arms.middle-proxy.url`**(Feign 대상), `slack.*`.

> ⚠️ **`RedisConfig` 는 Boot 3 에서 제거된 구키를 직접 읽는다.**
>
> ```java
> @Value("${spring.redis.host}")            // Boot 3 표준은 spring.data.redis.host
> @Value("${spring.redis.port}")
> @Value("${spring.redis.ssl.enabled:false}")
> ```
>
> 기본값이 없는 host/port 가 주입되지 않으면 **컨텍스트 생성 단계에서 기동 실패**한다.
> `application-dev.yml` 이 `spring.data.redis` 와 `spring.redis` 를 **둘 다** 적어 놓은 이유가 이것이다.
> 한쪽만 지우면 뜨지 않는다. 또한 dev yml 은 `spring.redis.ssl.enable` 이라 적혀 있는데
> 코드는 `...ssl.enabled` 를 읽는다 — **키 이름이 어긋난 죽은 설정**이다(기본값 false 라 조용히 넘어간다).

`spring.config.import` 가 `optional:` 이므로 Config 서버가 없어도 부팅은 시도하지만,
위 값들이 비면 그 다음 단계에서 실패한다.

상세: `references/build-and-ops.md`

---

## 9. 실행해서 확인하기

```bash
# 컴파일만 (가장 빠른 검증)
gradlew.bat compileJava          # Bash: ./gradlew compileJava
```

- **`build` 전체를 그냥 돌리지 말 것.** `build.gradle` 의 `ext` 블록이 Nexus 에서
  `metadata.xml` 을 `wget` 으로 받아 버전을 산정한다. Windows·Mac 은 스킵하고 동봉 파일을 쓰지만,
  Linux 는 네트워크가 필요하다. 버전은 `majorVersion=26` / `minorVersion=9` + metadata 기준 자동 patch.
- 로컬 구동: Active Profile **`dev`**. Redis 는 `www.313.co.kr:36379` 를 본다.
- 확인: `GET /api/health/redis` → `"Redis connection is OK"`,
  Actuator `/actuator/{health,env,beans,refresh}`.
- **테스트가 하나도 없다.** `OtUtils` · `TextOperation` 은 순수 함수이므로
  스프링 없는 JUnit 5 단위 테스트가 가장 값싼 검증이다(`useJUnitPlatform()` 은 이미 설정돼 있다).

---

## 10. 제출 전 자가 점검

- [ ] `jakarta.*` 를 썼는가? (`javax.*` 는 이 저장소에서 컴파일 안 된다)
- [ ] 컨트롤러가 값을 직접 반환하는가? (`Mono`/`Flux` 는 Middle-Proxy 규칙이다)
- [ ] STOMP 목적지를 바꿨다면 서버 3곳(`EditorController`·`OtController`·`WebSocketEventListener`)과
      프론트 `session-manager.js` 를 모두 반영했는가?
- [ ] 락 관련 변경이면 실제 수정 지점이 Middle-Proxy 인지 먼저 판별했는가?
- [ ] Redis 키를 추가했다면 TTL·정리 주체·클러스터 해시태그를 정했는가?
- [ ] `RedisTemplate`(JSON)과 `StringRedisTemplate`(문자열)이 같은 키를 건드리지 않는가?
- [ ] 인스턴스 로컬 상태(static 필드 · 인스턴스 락)를 새로 늘리지 않았는가?
- [ ] 새 설정 키가 필요하면 Global-Config 변경 필요를 보고했는가?
- [ ] 예외를 삼키는 자리(락 폴백 · Redis 실패)에서 **조용한 실패**를 만들지 않았는가? 로그는 남겼는가?
- [ ] 로깅 방식을 그 파일의 기존 것(SLF4J 또는 JUL)에 맞췄는가?
- [ ] 시크릿(Sonar 자격증명 · `SLACK_TOKEN`)을 코드·로그·문서에 복제하지 않았는가?

---

## 11. 산출 및 인계

- 사용자 대상 설명은 **한국어**로 한다.
- **commit·push 하지 않는다.** 작업 요약과 커밋 메시지 초안만 제시하고 커밋은 사용자가 한다.
  이 저장소의 실제 컨벤션(YouTrack 연동):

  ```
  feat : [ARMS-1195] #comment✅문서 저장시 락 해제 안되는 문제 2026.09.10 #close #time 1h +review SR @sevoon0909
  feat: [ARMS-223] #comment 위키 편집락 기능 추가 2026.08.22 #close #time 1h +review SR @sevoon0909
  ```

  현재 작업 브랜치는 `dev` 다(`main` 아님).
- 확신이 없는 지점(Config 서버가 주입하는 실제 값, 게이트웨이 라우트 정의, 프론트 동작)은
  추측으로 메우지 말고 **가정을 명시**하거나 질문한다.

---

## 12. 참조 파일 지도

| 파일 | 언제 읽나 |
|------|----------|
| `references/pitfalls.md` | 이상 동작이 보일 때 / 착수 전 함정 확인 (**먼저 읽으면 시간을 가장 많이 아낀다**) |
| `references/stomp-contract.md` | 채널·페이로드·토픽을 추가/변경할 때. DTO 필드 전수 목록 |
| `references/ot-engine.md` | 동시편집이 깨질 때. transform/apply/compose 규칙과 리비전 모델 |
| `references/redis-and-state.md` | Redis 키·직렬화·참가자 레지스트리·세션 생명주기를 다룰 때 |
| `references/lock-delegation.md` | 편집락 관련 작업 전부. Middle-Proxy 와의 계약 대조표 |
| `references/build-and-ops.md` | 빌드·버전·Docker·설정 주입·로깅·모니터링·Slack |

이 저장소에는 자체 문서가 없다. 연관 저장소가 보조 정본이다 —
Middle-Proxy `docs/ai/06_domain_playbooks/wiki-lock.md`(락 소유자 관점),
프론트 `Java-Service-Tree-Framework-Frontend-Web/arms/js/adms/session-manager.js` ·
`arms/js/adms.js`(클라이언트 정본).
