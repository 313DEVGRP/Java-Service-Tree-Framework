# 이 저장소에서 반복적으로 사람을 무는 함정

증상 → 원인 → 해결 순서로 정리한다. 이상 동작이 보이면 여기부터 확인한다.
(저장소 자체 `docs/ai/12_known_issues/guide.md` 에도 누적본이 있다. 새 함정은 양쪽에 남긴다.)

---

## A. 리액티브

### A-1. 부하가 걸리면 전 서비스가 느려진다
- **원인:** Redis/Kafka/Feign 블로킹 호출이 Netty 이벤트 루프 스레드에서 실행됨.
- **해결:** `Mono.fromCallable(...).subscribeOn(Schedulers.boundedElastic())`.
  이 저장소는 게이트웨이라 **한 곳의 블로킹이 전 모듈 트래픽을 막는다.** 다른 저장소보다 훨씬 치명적이다.

### A-2. `HttpServletRequest` 가 안 들어온다 / 보안 설정이 안 먹는다
- **원인:** MVC 습관. 이 저장소는 WebFlux.
- **해결:** `ServerHttpRequest` · `ServerWebExchange` · `ServerHttpSecurity`.
  `Application` 의 `UserDetailsServiceAutoConfiguration` 제외를 되살리지 않는다.

### A-3. `@RequestBody` 로 받았는데 본문이 비어 있다
- **원인:** 게이트웨이 경로를 거치며 본문이 이미 소비됐거나, `x-www-form-urlencoded` 로 들어옴.
- **해결:** `RequestBodyExtractor.extract(ServerHttpRequest)` 를 쓴다. 단, 본문은 **한 번만** 읽을 수 있으므로
  같은 요청에서 `@RequestBody` 와 병용하지 않는다.

### A-4. `@Async` 메서드인데 비동기로 안 돈다
- **원인:** 같은 빈 내부 호출(self-invocation)은 프록시를 안 탄다.
- **해결:** 다른 빈으로 분리해서 호출한다(`ReqDefRowNotifier` · `WbsRowNotifier` 가 그 예).

---

## B. 게이트웨이 · 보안

### B-1. 새 경로가 404 인데 코드엔 컨트롤러가 있다
- **원인:** 게이트웨이 라우트가 같은 접두를 다운스트림으로 가로채고 있다.
  (`/auth-user/**` 는 원래 Backend-Core 로 가는 라우트다.)
- **해결:** 자체 컨트롤러 경로가 라우트 predicate 와 겹치지 않는지 확인.
  겹치면 Global-Config 라우트 조정이 필요하다. 이 저장소만 고쳐서는 안 된다.

### B-2. 라우트만 추가 → 401 / 보안만 추가 → 연결 안 됨
- **원인:** 라우트(Global-Config)와 `SecurityConfiguration.pathMatchers` 중 한쪽만 변경.
- **해결:** 항상 양쪽을 짝으로 본다.

### B-3. `hasRole("ADMIN")` 인데 항상 403
- **원인:** Keycloak realm role 이 `ROLE_` 로 시작하지 않으면 권한 매핑에서 **버려진다**
  (`mapRolesToGrantedAuthorities` 가 `startsWith("ROLE_")` 로 필터).
- **해결:** realm role 이름을 `ROLE_ADMIN` 형태로 맞춘다.

### B-4. 내부 전용 API 가 인터넷에 열려 있다
- **원인:** `/poc/**`, `/wbs/**`, `/req-def/**`, `/wiki/lock/**`, `/atlassian/**`, `/mapping/**`,
  `/actuator/**` 가 전부 `permitAll` 이다(내부망 전제).
- **해결:** 새 경로를 permitAll 에 넣기 전에 외부 노출 여부를 반드시 확인한다.
  `actuator` 는 코드 주석에도 "향후 IP 제한 필요"라고 남아 있다.

### B-5. 로그아웃해도 Keycloak 세션이 안 끊긴다
- **원인:** `KeycloakLogoutHandler` 의 end-session URL 이 `http://keycloak:8080/auth` 로 **하드코딩**되어 있다
  (주입받은 `serverUrl` 을 쓰지 않는다). 컨테이너 밖에서는 항상 실패한다.
- **해결:** 로컬 세션은 정상 정리되므로 기능은 동작한다. 실제 SSO 로그아웃이 필요하면 이 상수를 고친다.

### B-6. `pathMatchers` 를 추가했는데 안 걸린다
- **원인:** 더 포괄적인 규칙(`/auth-user/**`)이 위에 있어 먼저 매칭됐다.
- **해결:** 구체적인 규칙을 위로 올린다.

---

## C. Redis

### C-1. 조회했더니 다른 도메인 데이터가 섞여 나오거나 역직렬화가 터진다
- **원인:** `excelUpload` 키스페이스를 **ExcelUploadFileVO · WbsRowVO · ReqDefRowVO 셋이 공유**한다.
  `findAll()` 이 세 타입을 다 긁어온다.
- **해결:** `scan("wbs:{id}:*")` / `scan("reqdef:{id}:*")` + `findAllById`.
  `deleteAll()` 대신 `deleteByPattern(...)`.

### C-2. 락이 안 풀린다 (업로드가 영원히 "진행 중")
- **원인 후보:**
  1) 예외 경로에서 `release` 를 안 부름,
  2) 콜백이 안 와서 드레인 판정이 안 남,
  3) 다른 토큰이라 `deleteIfEquals` 가 false 를 반환.
- **해결:** TTL 5분이 지나면 자연 만료된다. 즉시 풀어야 하면 Redis 에서
  `excelUpload:lock:{feature}:{pdServiceId}` 를 직접 삭제. 코드 수정 시에는
  `try/catch` 의 **모든 실패 경로**에서 `uploadLock.release(...)` 가 불리는지 확인한다.
- **주의:** `releaseLockIfDrained` 는 락 해제에 성공했을 때만 후속(빈 분류 정리·완료 알림)을 수행한다.
  해제 실패 시 조용히 스킵되고 경고 로그만 남는다.

### C-3. 방식 A/B 혼용으로 데이터가 안 보인다
- **원인:** 같은 논리 데이터를 `@RedisHash` 와 `@RedisEntity` 양쪽으로 접근.
  키 구조도 직렬화도 완전히 다르다.
- **해결:** 도메인당 한 방식. `RedisTemplate` 직접 호출 금지.

### C-4. 커스텀 프레임워크 엔티티에 필드를 추가했는데 기존 데이터가 깨진다
- **원인:** 기존 Hash 에 그 필드가 없다(→ `null` 로 남아 정상) 또는 타입을 바꿨다(→ 파싱 실패).
- **해결:** 타입 변경 시 `convertField(...)` 오버라이드로 구형 포맷을 흡수한다
  (`ChatRoomRepository` 의 `pdServiceVersionIds` 사례).
  `@RedisIgnore` 로 저장 제외도 가능하다.

### C-5. `@RedisEntity` 엔티티에 `@RedisId` 를 안 붙였다
- **증상:** 기동 시 `IllegalStateException: ... 에 @RedisId 가 없습니다.`
- **해결:** ID 필드에 `@RedisId`. 정렬이 필요하면 `@RedisScore`(int/long)도.

### C-6. `deleteIfFieldEquals` 가 항상 false
- **원인:** 대상 값이 JSON 문자열이 아니다(Lua 가 `cjson.decode` 한다).
  `@RedisHash` 로 저장한 Hash 에는 쓸 수 없다.
- **해결:** `setIfAbsent` 로 직접 넣은 String 값에만 사용한다(위키 락 패턴).

---

## D. Kafka

### D-1. 메시지를 보냈는데 DB 에 반영이 안 된다
- **원인 후보:** Backend-Core Consumer 의 `switch` 에 해당 `operation` 이 없음(조용히 버려짐) /
  `payload` 스키마 불일치 / Consumer 자체 오류.
- **해결:** Middle-Proxy 로그의 `requestId` 로 Backend-Core 로그를 대조한다.
  operation 추가는 **반드시 양쪽 동시 변경**.

### D-2. 요구사항 순서가 뒤바뀐다
- **원인:** REQADD 토픽 파티션을 1에서 늘렸다.
- **해결:** 단일 파티션 유지. 메시지 키는 `changeReqTableName`.

### D-3. 발행 실패인데 HTTP 200 이 온다
- **원인:** 발행 실패를 `Mono.error` 가 아니라 **성공 값(에러 Map)** 으로 돌려준다.
- **해결:** 호출부는 상태코드가 아니라 본문의 `status` 필드를 본다.
  `subscribe(onSuccess, onError)` 의 onError 가 안 탈 수 있음을 염두에 둔다.

### D-4. 기동 시 Kafka 빈 충돌
- **원인:** `Application` 의 `KafkaAutoConfiguration` 제외를 풀었다.
- **해결:** 제외를 유지하고 `config/KafkaConfig` 만 정본으로 둔다.

### D-5. 엑셀 업로드에서 자식 노드가 안 생긴다
- **원인:** 부모 콜백(`publish-kafka-from-parent-node`)이 오지 않았다 —
  Backend-Core 가 콜백을 못 보냈거나, `uploadToken` 불일치로 지각 콜백 판정되어 무시됨.
- **해결:** 락 토큰이 업로드마다 새로 발급되므로, 이전 업로드 콜백은 **의도적으로 무시**된다.
  로그 `[ReqDef 콜백] 이전 업로드의 콜백으로 판단하여 무시` 를 확인한다.

---

## E. Feign

### E-1. Feign 호출이 런타임에 터진다 (`@RequestBody` 사용 시)
- **원인:** WebFlux 라 `HttpMessageConverters` 가 없고, 이 저장소는 **Decoder 만** 등록한다.
- **해결:** `@RequestParam` / `@PathVariable` 로 보낸다.

### E-2. 한글 인터페이스명을 못 찾는다
- **해결:** `엔진통신기` 처럼 한글 그대로 grep 한다. 이 저장소는 한글 식별자를 쓴다.

---

## F. 빌드 · 문서

### F-1. 기동 시 Swagger 관련 `ClassCastException`
- **원인:** Springfox 3.0.0 + Boot 2.6 비호환.
- **해결:** `Swagger2Config.springfoxHandlerProviderBeanPostProcessor()` 를 **삭제하지 않는다.**

### F-2. `./gradlew build` 가 실패한다
- **원인 후보:** Nexus 메타데이터 접근 불가 / `licenseReport` 가 참조하는
  **`allowed-licenses.json` 이 저장소에 없다** / Sonar 접속 불가.
- **해결:** 코드 검증만 필요하면 `./gradlew compileJava` 로 충분하다.

### F-3. 로컬에서 산정된 버전이 이상하다 (`26.0.0`)
- **원인:** Windows·Mac 은 Nexus 메타데이터를 받지 않고 커밋된 `metadata.xml`(latest `0.0.1`)을 읽는다.
  `majorVersion(26) > 0` 이라 minor·patch 가 0 으로 초기화된다.
- **해결:** 정상이다. 실제 버전은 Linux CI 에서 산정된다.

### F-4. dev 프로파일로 띄우면 로그 파일 경로 오류
- **원인:** `logback-dev.xml` 의 FILE 어펜더가 `/Users/leemingyu/dev/logs/arms-mp.log` 로 하드코딩됨.
- **해결:** 로컬에서 경로를 바꾸되 **커밋하지 않는다.**

### F-5. Config 서버에 못 붙으면 기동 실패
- **원인:** `import: optional:configserver:` 라 import 실패는 무시되지만,
  `@Value("${spring.security.auth.success.redirect-url}")` 같은 필수 주입이 없어 컨텍스트가 터진다.
- **해결:** dev 는 `www.313.co.kr:33133` 에 도달 가능해야 한다.

### F-6. 문서와 코드의 관계
- `docs/ai/` 와 루트 `README.md` · `REQADD_KAFKA_INTEGRATION.md` 는 2026-09-22 코드 전수 대조로 정합화됐다.
- 그래도 **코드가 정본이다.** 어긋난 것을 발견하면 문서를 고치고
  `docs/ai/11_changelog` 와 `docs/ai/12_known_issues` 에 남긴다.
- 폐기 상태(삭제 대기): `docs/ai/06_page_playbooks/`, `docs/ai/06_domain_playbooks/issue-buffer.md`.

---

## G. 보안 위생

- `aes.token` · `slack.token` · Keycloak `client-secret` 은 Global-Config 주입 yml 에 평문으로 들어 있다.
  `build.gradle` 의 Sonar 계정도 평문이다. **값을 문서·로그·커밋·외부 채널에 복제하지 않는다.**
  코드는 키 경로(`${aes.token}`)만 참조한다.
- `AES256.encrypt` 는 키가 비어 있으면 **평문을 그대로 반환**한다. 암호화가 조용히 무력화될 수 있으니
  새 암호화 대상에는 키 주입 여부를 확인한다.
- `certs/` 아래 실제 인증서와 개인키(`*.key`, `*.pfx`)가 커밋되어 있다. 외부로 옮기지 않는다.
