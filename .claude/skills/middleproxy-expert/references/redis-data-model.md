# Redis 데이터 모델과 저장소 API

정본: `config/RedisConfig`, `api/util/redisrepo/**`, 각 도메인 `repository`·`model`.

이 저장소의 **영속 계층은 Redis 하나뿐**이다. RDB·JPA·OpenSearch 를 직접 쓰지 않는다.

---

## 1. RedisConfig 가 등록하는 빈

```java
@Configuration @EnableWebFlux
@EnableRedisRepositories(basePackages = "com.arms", repositoryBaseClass = BaseRedisRepository.class)
@EnableRedisWebSession(maxInactiveIntervalInSeconds = 60 * 60 * 2)
public class RedisConfig {
  StringRedisTemplate                 stringRedisTemplate   // String/String
  RedisTemplate<String, Object>       redisTemplate         // key=String, value=GenericJackson2Json
  ReactiveRedisTemplate<String,Object> reactiveRedisTemplate
  RedisScript<Boolean>                updateContentAndHistoryScript  // SET + RPUSH + LTRIM (Lua)
}
```

- `@EnableRedisRepositories(repositoryBaseClass = BaseRedisRepository.class)` 가 핵심이다.
  이것 때문에 모든 Spring Data Redis 레포지토리가 `scan` · `setIfAbsent` 같은 확장 기능을 갖는다.
- `updateContentAndHistoryScript` 는 본문 저장 + 히스토리 RPUSH + 최대 길이 LTRIM 을
  원자적으로 처리하는 Lua 스크립트다(위키 편집 계열에서 사용 가능).

---

## 2. 방식 A — Spring Data Redis (`@RedisHash`)

### 2.1 엔티티

```java
@Getter @Builder @AllArgsConstructor @NoArgsConstructor
@RedisHash(value = "atlassian", timeToLive = 60 * 60 * 24 * 3)   // 초 단위 TTL (선택)
public class AtlassianDirectoryUserEntity {
    @Id private String id;                 // 실제 키 = "atlassian:{id}"
    private String accountId;
    private String email;
    public static String idOf(String connectId, String accountId) { return connectId + ":" + accountId; }
}
```

### 2.2 레포지토리

```java
public interface XxxRepository extends CustomRedisTemplate<XxxVO, String> {}
```

`CustomRedisTemplate<T, ID>` = `CrudRepository<T, ID>` + 아래 확장.

| 메서드 | 동작 | 비고 |
|--------|------|------|
| `List<String> scan(String pattern)` | `keySpace:pattern` 으로 SCAN(count 200), **키스페이스를 벗긴 id 목록** 반환 | `findAll()` 대신 쓴다 |
| `void deleteByPattern(String pattern)` | scan 결과를 하나씩 delete | |
| `String getKeySpace()` | `@RedisHash` 의 value | |
| `boolean setIfAbsent(subKey, value, Duration ttl)` | `SET key value PX ttl NX` | 락 획득 |
| `boolean deleteIfEquals(subKey, expected)` | 값이 같을 때만 DEL (Lua) | 락 해제 |
| `boolean expireIfEquals(subKey, expected, ttl)` | 값이 같을 때만 PEXPIRE (Lua) | 락 연장 |
| `String getValue(subKey)` / `Long getExpireMillis(subKey)` | GET / PTTL | |
| `boolean deleteIfFieldEquals(subKey, field, expected)` | **값이 JSON 일 때** 해당 필드가 일치하면 DEL | |
| `boolean expireIfFieldEquals(subKey, field, expected, ttl)` | 같은 조건으로 PEXPIRE | |
| `boolean setFieldIfFieldEquals(subKey, matchField, expected, targetField, value, ttl)` | 조건 일치 시 다른 필드 수정 후 재저장 | |
| `boolean deleteIfFieldOlderThan(subKey, field, fallbackField, nowMillis, thresholdMillis)` | 타임스탬프 필드가 오래됐으면 DEL | 유휴 락 takeover |

> 전체 키는 `{keySpace}:{subKey}` 로 조립된다(`fullKeyOf`).
> `deleteIfField*` 계열은 값이 **`cjson.decode` 가능한 JSON 문자열**일 때만 동작한다.
> `@RedisHash` 로 저장한 Hash 구조에는 쓸 수 없다 — `setIfAbsent` 로 직접 넣은 값에만 쓴다.
> 파이프라인/트랜잭션 모드에서는 `inRedis(...)` 가 null 을 돌려줄 수 있다.

---

## 3. 방식 B — 커스텀 Redis Hash 프레임워크 (`api/util/redisrepo`)

### 3.1 구성 요소

```
RedisFramework            ─ string()/hash()/list()/set()/zSet() + expire/delete/hasKey 진입점
RedisHashRepository       ─ Hash 명령 단일 진입점 (HMSET/HGETALL/HSET/HGET/HKEYS/HDEL/HLEN/HINCRBY,
                            getAll(keys) 는 파이프라인으로 N개 HGETALL 을 1 round-trip 처리)
RedisStringCommand / RedisListCommand / RedisSetCommand / RedisZSetCommand
AbstractRedisHashRepository<T, ID>  ─ 엔티티 CRUD 자동 제공 (상속해서 쓴다)
annotation/ @RedisEntity @RedisId @RedisScore @RedisIgnore
util/ KeyName, RedisUtil
```

### 3.2 어노테이션

| 어노테이션 | 대상 | 의미 |
|-----------|------|------|
| `@RedisEntity(value, ttlDays = 0)` | 클래스 | namespace(키 접두)와 TTL(일). **필수**. 0 = 영구 |
| `@RedisId` | 필드 | ID. **필수** (없으면 생성자에서 `IllegalStateException`) |
| `@RedisScore` | 필드 | 인덱스 score(int/long). `getAll()` 오름차순 정렬 기준 |
| `@RedisIgnore` | 필드 | 직렬화 제외 |

### 3.3 키·직렬화 규칙

```
엔티티  {namespace}:{id}     → Hash { 필드명: 값, 필드명: 값, ... }
인덱스  {namespace}:index    → Hash { id: score }
```

- 단순 타입(`String`/`int`/`long`/`double`/`boolean` + 래퍼) → `String.valueOf()` 로 그대로.
- `List`/`Map`/중첩 객체 → Jackson JSON. 역직렬화 시 `getGenericType()` 으로 제네릭까지 복원.
- `null` 필드는 저장하지 않는다(HSET 자체를 건너뜀).
- `static` · `synthetic` 필드는 제외. 부모 클래스 필드까지 수집.
- **구형 호환:** Hash 에 `data` 필드 하나만 있으면 그 값을 엔티티 전체 JSON 으로 역직렬화한다.

### 3.4 제공 메서드 (대표)

| 분류 | 메서드 |
|------|--------|
| 기본 | `save(entity)` · `getById(id)` · `getAll()` · `getByIds(ids)` · `deleteById(id)` · `deleteAll()` |
| 부분 수정 | `updateField(id, fieldName, value)` (HSET) · `increment(id, field, delta)` (HINCRBY, 원자적) |
| 조합 | `merge(id, modifier, defaultSupplier)` — "조회 → 없으면 생성 → 수정 → 저장" 한 번에 |
| Map 필드 | `putMapEntry` · `removeMapEntry` · `popMinMapEntry` · `popMaxMapEntry` |
| List 필드 | `appendListEntry` · `removeListElement` · `findListField` |
| 정렬·TTL | `findSortedKeys` · `refreshExpiry` |

`getAll()` 은 `{ns}:index` 로 id 를 모은 뒤 `RedisHashRepository.getAll(keys)` 파이프라인으로
한 번에 읽는다 — **N+1 이 없다.** 직접 루프를 돌며 `getById` 를 부르지 않는다.

### 3.5 역직렬화 커스터마이징

`convertField(fieldName, rawValue, field)` 를 오버라이드하면 구형 데이터 포맷을 흡수할 수 있다.

```java
@Override
protected Object convertField(String fieldName, String rawValue, Field field) {
    if ("pdServiceVersionIds".equals(fieldName) && !rawValue.startsWith("[")) {
        return rawValue.trim().isEmpty() ? null : Arrays.asList(rawValue.split(","));   // 구형: "a,b"
    }
    return super.convertField(fieldName, rawValue, field);                               // 신형: ["a","b"]
}
```

---

## 4. 키스페이스 상세

| 키 | 구조 | 소유 |
|----|------|------|
| `ai:chat:room:{roomId}` | Hash (ChatRoom) | aichat, TTL 30일 |
| `ai:chat:room:index` | Hash `{roomId: updatedAt}` | aichat |
| `ai:chat:messages:{roomId}` | Hash (ChatMessageList, messages 는 JSON 배열) | aichat, 최대 20개 |
| `ai:chat:rooms:default:{userId}` | Hash (ChatRoomList) | aichat, 최대 10개 |
| `ai:chat:recommended-cards` | Hash (RecommendedCard) | aichat, TTL 없음 |
| `ai:chat:last-selection:{userId}` | Hash (LastSelection) | aichat |
| `ai:chat:room-rag:{roomId}` | Hash (RagDocs) | aichat |
| `excelUpload:wbs:{pdServiceId}:{wbs}:{jobName}` | Hash (WbsRowVO) | wbs |
| `excelUpload:reqdef:{pdServiceId}:{classLevelKey}` | Hash (ReqDefRowVO) | reqdef |
| `excelUpload:wbs:{pdServiceId}` / `excelUpload:reqdef:{pdServiceId}` | Hash (ExcelUploadFileVO, 업로드 파일 경로) | excelupload |
| `excelUpload:lock:wbs:{pdServiceId}` / `:lock:reqdef:{pdServiceId}` | String (uploadToken), TTL 5분 | excelupload 락 |
| `almIssueStatus:{serverId}-{projectKey}-{issueTypeId}-{issueStatusId}` | Hash | mapping |
| `state:{id}` · `category:{id}` | Hash | mapping |
| `pocReqRegister:{id}` | Hash | poc |
| `atlassian:{connectId}:{accountId}` | Hash, TTL 3일 | atlassian (email AES256) |
| `wiki:lock:{sessionId}:{documentId}` | **String(JSON)**, TTL 120초 | wiki 락 |
| `spring:session:sessions:{id}` | Hash | Spring Session, 2시간 |

> ⚠️ `excelUpload` 한 키스페이스에 **세 가지 엔티티 타입**이 섞여 있다.
> `findAll()` / `deleteAll()` 을 부르면 다른 도메인 데이터까지 잡아먹거나 역직렬화가 깨진다.
> 반드시 `scan("wbs:{id}:*")` 처럼 접두를 좁혀서 쓴다(`WbsRowId` · `ReqDefRowId` · `ExcelUploadKey` 참고).

---

## 5. 분산 락 두 종류

### 5.1 엑셀 업로드 락 (`ExcelUploadLock`)

```java
String token = uploadLock.tryAcquire(ExcelUploadFeature.REQDEF, pdServiceId);  // UUID, TTL 5분
uploadLock.renew(feature, pdServiceId, token);     // 내 토큰일 때만 연장 (expireIfEquals)
uploadLock.release(feature, pdServiceId, token);   // 내 토큰일 때만 해제 (deleteIfEquals)
```

- 토큰(`uploadToken`)은 업로드 세션 식별자로도 쓰인다. 각 행 VO 에 저장되어
  **지각 콜백을 구분**하는 근거가 된다.
- 획득 실패 시 `null` 반환 — 호출부가 "이미 업로드 진행 중" 으로 응답한다.

### 5.2 위키 편집 락 (`WikiLockService`)

- 키: `wiki:lock:{sessionId}:{documentId}`, 값은 JSON
  `{holderId, holderName, acquiredAt, lastActivityAt}`, TTL 120초.
- `acquire` 는 최대 2회 시도(SET NX 와 GET 사이의 만료 경합 대비). 같은 사용자면 재진입 허용.
- `release` 는 `deleteIfFieldEquals(subKey, "holderId", userId)` 로 **소유자만** 해제.
- `touchActivity` 는 `setFieldIfFieldEquals` 로 `lastActivityAt` 갱신.
- `forceRelease` 는 `deleteIfFieldOlderThan` 으로 60초(`TAKEOVER_IDLE_MILLIS`) 이상
  유휴일 때만 강탈 허용.

새 락을 만들 때는 이 두 패턴 중 하나를 그대로 따른다. `RedisTemplate` 으로 직접 SETNX 하지 않는다.

---

## 6. 하지 말 것

- 서비스·컨트롤러에서 `RedisTemplate` / `StringRedisTemplate` 직접 주입·호출.
- 한 도메인에서 방식 A 와 B 혼용.
- `@RedisHash` 엔티티에 `keys *` 스타일의 전체 조회(`findAll`) — 특히 `excelUpload`.
- TTL 이 있는 엔티티를 저장하면서 `refreshExpiry` / `renew` 를 빼먹기
  (긴 작업 도중 락이나 데이터가 만료된다).
- 키 문자열을 코드 여기저기서 조립하기 — `AiChatRedisKeys`, `ExcelUploadKey`,
  `WbsRowId`, `ReqDefRowId` 같은 키 객체/상수를 쓴다.
