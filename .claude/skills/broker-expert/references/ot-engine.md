# OT 엔진 (Operational Transformation)

`ot.js` 의 `TextOperation` 을 Java 로 포팅한 것이다.
파일 두 개가 전부다 — `api/util/OtUtils.java`(순수 함수) · `api/wiki/dto/TextOperation.java`(자료구조).
`api/wiki/service/OtService.java` 가 이 둘을 Redis 상태에 얹는다.

---

## 1. `TextOperation` 표현

op 리스트 하나에 세 종류를 **타입으로 구분해** 섞는다.

| 값 | 의미 | 예 |
|----|------|-----|
| 양수 `Integer` | retain — n글자 건너뛰기 | `5` |
| `String` | insert — 문자열 삽입 | `"abc"` |
| 음수 `Integer` | delete — n글자 삭제 | `-2` |

```
[5, "abc", -2]   =  앞 5글자 유지 → "abc" 삽입 → 이어지는 2글자 삭제
```

### 불변식

| 필드 | 의미 | 갱신 |
|------|------|------|
| `baseLength` | 적용 **전** 문서 길이 | retain(+n) · delete(+n) |
| `targetLength` | 적용 **후** 문서 길이 | retain(+n) · insert(+len) |

`apply(doc, op)` 는 `doc.length() == op.baseLength` 를 요구하고
(정확히는 소비 후 인덱스가 문서 끝에 도달해야 하고),
`compose(a, b)` 는 `a.targetLength == b.baseLength`,
`transform(a, b)` 는 `a.baseLength == b.baseLength` 를 요구한다.

### 빌더의 정규화 규칙 (직접 리스트를 만들지 말 것)

`retain` / `insert` / `delete` 메서드는 **정규형을 유지한다.**

- 같은 종류가 연속되면 **병합**한다 (`retain(3).retain(2)` → `[5]`).
- `retain(0)` · `insert("")` · `delete(0)` 은 **무시**된다.
- `insert` 는 마지막이 delete 면 **delete 앞으로 끼워 넣는다** (insert-before-delete 정규화).
  ot.js 와 동일한 규칙이며, 이 순서가 깨지면 `transform` 결과가 상대와 어긋난다.
- `retain(음수)` 는 `IllegalArgumentException`.
- `delete(n)` 은 양수를 줘도 음수로 저장한다.

> ⚠️ `setOps(List)` 는 **길이를 재계산하지 않는다**(코드 주석에 경고 있음).
> 절대 쓰지 말고 `@JsonCreator` 생성자(`new TextOperation(list)`) 또는 빌더를 쓴다.
> 생성자는 리스트를 순회하며 빌더를 다시 호출하므로 정규화와 길이가 모두 보장된다.

### JSON 형태

`@JsonValue getOps()` + `@JsonCreator TextOperation(List<Object>)` 이므로
객체가 아니라 **배열**로 직렬화된다.

```json
[5, "abc", -2]
```

`getOps()` 는 **방어 복사본**을 돌려준다. 반환값을 수정해도 원본은 안 바뀐다.

---

## 2. `OtUtils` 네 함수

### `apply(String doc, TextOperation op) → String`

op 를 순서대로 소비하며 새 문서를 만든다. 실패 조건:
- `Retain exceeds document length.`
- `Delete exceeds document length.`
- `Invalid op type in operation: ...`
- `Operation did not consume the entire document.` ← 길이 불일치의 전형적 신호

### `transform(TextOperation a, TextOperation b) → List[a', b']`

동시에 발생한 두 op 에 대해 `apply(apply(S,a), b') == apply(apply(S,b), a')` 를 만족하는 쌍을 만든다.
**`a.baseLength == b.baseLength` 를 먼저 검사**하고 다르면 `IllegalArgumentException`.

우선순위 규칙: **insert 가 먼저 자리를 차지한다.**
`a` 의 insert 를 먼저 처리하므로, 같은 위치에 둘이 삽입하면 **`a`(= 새로 들어온 op)의 글자가 앞**에 온다.
이 비대칭이 tie-breaking 이며 서버가 항상 같은 순서로 적용하기 때문에 일관성이 유지된다.

### `compose(TextOperation a, TextOperation b) → TextOperation`

연속된 두 op 를 하나로 합친다. `a.targetLength == b.baseLength` 필요.
**현재 어디서도 호출되지 않는다**(히스토리 압축 등에 쓸 수 있는 재료).

### `invert(String doc, TextOperation op) → TextOperation`

원본 문서를 받아 되돌리는 op 를 만든다(undo 용). **현재 어디서도 호출되지 않는다.**

---

## 3. `OtService` — Redis 위의 OT

### 키

```java
CLUSTER_KEY_FORMAT = "doc:{%s}:%s:%s"     // {sessionId} 가 해시태그
content  → doc:{sessionId}:content:{documentId}
history  → doc:{sessionId}:history:{documentId}
```

`{}` 는 Redis Cluster 해시태그다. content 와 history 가 **같은 슬롯**에 놓여야
멀티키 Lua 스크립트가 돈다. 키 포맷을 바꿀 때 이 제약을 깨지 말 것.

### 리비전 = 히스토리 리스트 길이

```java
public int getRevision(String sessionId, String documentId) {
    Long size = historyListOperations.size(historyKey);   // LLEN
    return (size != null) ? size.intValue() : 0;
}
```

별도 카운터가 없다. **이 한 줄이 §5 의 결함을 만든다.**

### `receiveOperation` 전체 흐름

```
serviceLock.lock()                         ← 인스턴스 로컬 ReentrantLock
  ├ currentContent = GET content           (실패 시 "" 반환 — 예외 안 던짐)
  ├ serverRevision = LLEN history
  ├ 검증: 0 <= clientRevision <= serverRevision   아니면 IllegalArgumentException
  ├ clientRevision < serverRevision 이면
  │    LRANGE history clientRevision .. serverRevision-1
  │    각 원소(JSON 문자열) → objectMapper.readValue(List<Object>) → new TextOperation(list)
  │    for each: transformedOp = transform(transformedOp, concurrentOp)[0]
  ├ newContent = apply(currentContent, transformedOp)
  ├ transformedOpJson = objectMapper.writeValueAsString(transformedOp.getOps())
  └ Lua 원자 실행: SET content, RPUSH history, LTRIM(최대 500)
serviceLock.unlock()
→ 반환: transformedOp (컨트롤러가 방송)
```

### Lua 스크립트 (`RedisConfig.updateContentAndHistoryScript`)

```lua
local contentKey = KEYS[1]
local historyKey = KEYS[2]
redis.call('SET',   contentKey, ARGV[1])   -- newContent
redis.call('RPUSH', historyKey, ARGV[2])   -- operationJson
local maxHistory = tonumber(ARGV[3])
if maxHistory and maxHistory > 0 then
    local currentSize = redis.call('LLEN', historyKey)
    if currentSize > maxHistory then
        redis.call('LTRIM', historyKey, currentSize - maxHistory, -1)
    end
end
return true
```

content 와 history 를 **원자적으로** 갱신하기 위한 장치다. 이 원자성은 정확하다.
문제는 트림이 리비전 의미를 깨는 것이다(§5).

### 그 외 메서드

| 메서드 | 동작 | 호출처 |
|--------|------|--------|
| `getDocumentContent` | GET, 실패·부재 시 `""` | 여러 곳 |
| `getRevision` | LLEN, 실패 시 0 | 여러 곳 |
| `setDocumentContent` | SET content + **DEL history** (리비전 0 리셋) | `SessionController` |
| `resetSessionDocument` | content·history 동시 DEL | **미사용** |
| `getOperationHistory` | 전체 히스토리 역직렬화 | **미사용** |

---

## 4. 직렬화 경로 (한 번 더 감싸진다)

`RedisTemplate<String,Object>` 의 value serializer 는 `GenericJackson2JsonRedisSerializer` 다.
`OtService` 는 이미 JSON 문자열로 만든 op 를 이 템플릿으로 넘기므로 **한 번 더 감싸진다.**

```
TextOperation.getOps()  →  ObjectMapper  →  "[5,\"abc\",-2]"   (Java String)
                        →  GenericJackson2Json  →  Redis 에 저장되는 값
```

읽을 때 역순으로 풀리므로 자체적으로는 일관된다. 다만:

- 히스토리 원소가 `String` 이 아니면 `Unexpected non-string type found in history` 경고 후
  **그 원소를 건너뛴다** → op 유실 → 내용 분기. 다른 도구로 같은 키에 쓰지 말 것.
- JSON 파싱 실패는 `IllegalStateException` 을 던진다(`receiveOperation`).
  `getOperationHistory` 에서는 건너뛴다 — **두 경로의 정책이 다르다.**
- `SerializationException` 은 별도로 잡아 `RuntimeException` 으로 감싼다.

---

## 5. 알려진 결함 — 히스토리 트림 ⚠️

```
MAX_HISTORY_SIZE_PER_DOC = 500
리비전 = LLEN(history)
Lua 가 LLEN > 500 이면 LTRIM 으로 앞을 잘라낸다
```

**결과 1 — 리비전이 멈춘다.** 501번째 op 이후 `LLEN` 은 계속 500 이다.
서버는 영원히 "리비전 500" 을 보고하고, 클라이언트도 500 에 고정된다.

**결과 2 — 인덱스 의미가 어긋난다.** `LRANGE history clientRevision .. serverRevision-1` 은
"리비전 clientRevision 이후의 op 들"을 의도하지만, 트림 후 인덱스 0 은 리비전 0 이 아니다.
따라서 **엉뚱한 op 로 transform** 하게 되고, 각 클라이언트가 서로 다른 최종 문서를 갖는다.

**예외는 나지 않는다.** 길이가 우연히 맞으면 `apply` 도 통과한다.

### 재현

같은 문서에 500회 이상 op 를 보낸 뒤 두 브라우저로 동시 편집한다.

### 고칠 때의 설계 포인트

1. 리비전을 히스토리 길이에서 분리한다 — `doc:{sid}:rev:{did}` 를 `INCR` 로 관리.
2. 트림 시작 오프셋(`doc:{sid}:histbase:{did}`)을 같이 저장하고
   `LRANGE (clientRevision - base) .. (serverRevision - base - 1)` 로 보정한다.
3. `clientRevision < base` 인 클라이언트는 transform 불가이므로
   **전체 상태 재동기화**(state 토픽으로 full snapshot 재전송)로 강등해야 한다.
4. 1~3 은 Lua 스크립트와 클라이언트 프로토콜을 함께 바꾼다.
   **코드 몇 줄 수정이 아니라 설계 변경이다. 착수 전 사용자 확인을 받을 것.**

---

## 6. 검증 전략 — 테스트가 없다

`OtUtils` 와 `TextOperation` 은 **스프링·Redis 없이 테스트 가능한 순수 함수**다.
이 저장소에서 가장 값싼 검증 수단이며, `useJUnitPlatform()` 은 이미 설정돼 있다
(`src/test` 디렉토리를 만들면 된다).

핵심 속성(property):

```java
// 1. TP1 — 수렴성
apply(apply(S, a), transform(a, b).get(1)) == apply(apply(S, b), transform(a, b).get(0))

// 2. compose
apply(apply(S, a), b) == apply(S, compose(a, b))

// 3. invert
apply(apply(S, op), invert(S, op)) == S

// 4. 길이 불변식
apply(S, op).length() == op.getTargetLength()   // 단, S.length() == op.getBaseLength()
```

무작위 op 생성기로 1번을 수천 회 돌리면 포팅 오류가 대부분 드러난다.
새 로직을 넣기 전에 **현재 구현이 이 속성을 만족하는지 먼저 확인**하는 것을 권한다.
