# Kafka (REQADD) 프로듀서

정본: `config/KafkaConfig`, `api/kafka/reqadd/**`.
소비자는 이 저장소가 아니라 **Backend-Core** 에 있다.

---

## 1. 토픽·프로듀서 설정

```java
@Configuration @RefreshScope
public class KafkaConfig {
  @Value("${spring.kafka.bootstrap-servers:Kafka00Service:9094,Kafka01Service:9094,Kafka02Service:9094}")
  @Value("${spring.kafka.topic.reqadd:REQADD}")

  KafkaAdmin / AdminClient
  NewTopic reqAddTopic()   // partitions 1, replicas 3, retention 2419200000ms(4주), cleanup=delete
  KafkaTemplate<String,String>
  ProducerFactory<String,String>  // acks=all, retries=3, linger.ms=10, compression=lz4,
                                  // enable.idempotence=true, buffer.memory=32MB, StringSerializer x2
}
```

- `Application` 이 `KafkaAutoConfiguration` 을 제외하므로 **이 클래스가 유일한 Kafka 구성**이다.
  자동 구성을 되살리면 빈이 충돌한다.
- **파티션 1개는 의도된 설계다.** 요구사항 트리 변경의 순서 보장 때문. 늘리면 순서가 깨진다.
- 키·값 모두 `String`. 메시지 본문은 직접 JSON 직렬화한다.

---

## 2. 메시지 포맷 — `ReqAddKafkaMessage`

```java
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class ReqAddKafkaMessage {
    private String operation;            // ADD_NODE, UPDATE_NODE, ...
    private String changeReqTableName;   // T_ARMS_REQADD_{pdServiceId}  — 메시지 키로도 사용
    private String method;               // POST/PUT/DELETE (참고용)
    private String payload;              // 요청 본문 JSON 문자열 (ReqAddDTO 직렬화)
    private Long   timestamp;
    private String requestId;            // UUID, 추적용
    private String userId;               // (선택)
    private String fromAPI;              // 발행 출처 (선택)
}
```

`fromAPI` 실제 사용 값: `gantt-excel-upload` · `reqdef-excel-upload` · `poc-req-register`.
프론트에서 직접 온 요청은 비어 있다.

`payload` 에 들어가는 `ReqAddDTO` 의 주요 필드:
`ref`(부모 c_id) · `c_id` · `c_position` · `c_title` · `c_type`(`default`/`folder`) ·
`c_req_pdservice_link` · `c_req_pdservice_versionset_link` · `c_req_state_link` ·
`c_req_urgency_link` · `c_req_importance_link` · `c_req_difficulty_link` ·
`c_req_manager` · `c_req_contents` · `c_req_def_id` · `classLevelKey` · `wbsRowKey` · `uploadToken` ·
리뷰어 5쌍 · 일정/진척 필드 · ALM 이슈 연계 필드.

---

## 3. 발행 경로 세 갈래

| 컨트롤러 | 경로 | 서비스 | 특징 |
|----------|------|--------|------|
| `ReqAddProxyControllerSync` | `/auth-user/api/arms/reqAdd/sync/{table}/*.do` | `ReqAddProxyServiceImplSync` | `future.get()` 블로킹 → `boundedElastic` 격리. **파티션/오프셋 확인 후 응답** |
| `ReqAddProxyControllerAsync` | `/auth-user/api/arms/reqAdd/async/{table}/*.do` | `ReqAddProxyServiceImplAsync` | `ListenableFutureCallback` → 완전 논블로킹 |
| `ReqAddController` | `/kafka/reqAdd/{table}/*.do` | Sync 서비스 | `updateReqAddTitle.do`, `updateAllReqAddState.do` |

세 컨트롤러 모두 본문을 `RequestBodyExtractor` 로 추출한다(`@RequestBody` 아님).

### 엔드포인트별 operation

| 엔드포인트 | operation | method |
|-----------|-----------|--------|
| `sync|async/{table}/addNode.do` | `ADD_NODE` | POST |
| `sync/{table}/updateNode.do` | `UPDATE_NODE` | PUT (async 는 POST) |
| `sync|async/{table}/removeNode.do` | `REMOVE_NODE` | DELETE |
| `sync/{table}/moveNode.do` | `MOVE_NODE` | PUT (async 는 POST) |
| `sync/{table}/updateDataBase.do` | `UPDATE_DATABASE` | PUT |
| `sync/{table}/updateDate.do` | `UPDATE_DATE` | PUT |
| `/kafka/reqAdd/{table}/updateReqAddTitle.do` | `UPDATE_REQADD_TITLE` | PUT |
| `/kafka/reqAdd/{table}/updateAllReqAddState.do` | `UPDATE_ALL_REQADD_STATE` | PUT |
| (내부) PocReqRegisterService | `ADD_NODE_SKIP_ALM` | POST |

> `method` 값이 sync/async 사이에 일관되지 않다(`UPDATE_NODE` 가 한쪽은 PUT, 한쪽은 POST).
> Consumer 가 `operation` 으로만 분기하므로 현재 문제는 없지만, 새 코드에서는 sync 쪽 값에 맞춘다.

---

## 4. 응답 포맷

성공:

```json
{
  "status": "ACCEPTED",
  "message": "Request queued for processing",
  "requestId": "<uuid>",
  "operation": "ADD_NODE",
  "table": "T_ARMS_REQADD_123",
  "timestamp": 1700000000000,
  "kafka": { "partition": 0, "offset": 12345 }     // async 서비스에만 포함
}
```

실패(직렬화/발행 오류):

```json
{ "status": "INTERNAL_SERVER_ERROR", "code": 500, "message": "...", "requestId": "...", "timestamp": ... }
```

> ⚠️ **실패해도 `Mono.error` 가 아니라 `sink.success(errorMap)` / `Mono.just(errorMap)` 로 돌려준다.**
> 즉 HTTP 상태는 200 이고 본문의 `status` 필드로만 실패를 알 수 있다.
> 호출부(프론트·내부 서비스)는 상태코드가 아니라 본문을 봐야 한다.
> `ReqDefNodePublisher` 같은 내부 호출부가 `subscribe(onSuccess, onError)` 의 onError 를
> 기대하고 있다면, 발행 실패가 그 분기로 오지 않을 수 있다는 점을 염두에 둔다.

---

## 5. 콜백 기반 순차 등록 (엑셀 업로드)

트리 구조를 Kafka 로 만들 때는 **부모가 실제로 DB 에 생긴 뒤에야 자식의 `ref`(부모 c_id)를 알 수 있다.**
그래서 이 저장소는 "루트만 발행 → Backend-Core 가 콜백 → 자식 발행" 을 반복한다.

```
Middle-Proxy                         Backend-Core
  publish(ADD_NODE, 루트)  ──────▶  consume → 노드 생성
                           ◀──────  POST /req-def/publish-kafka-from-parent-node
                                     (또는 /wbs/publish-kafka-from-parent-node)
  markConsumed(부모행)
  renewLock
  publish(자식들, ref=부모 c_id)  ─▶ ...
```

콜백 VO (`ReqDefCallbackReqVO` / `WbsCallbackReqVO`) 가 담는 것:
`cId`(생성된 노드 id) · `cReqPdServiceLink`(pdServiceId) · `classLevelKey` 또는 `rowKey` ·
`uploadToken` · 실패 여부.

방어 규칙:

- `uploadToken` 이 현재 저장된 행의 토큰과 다르면 **이전 업로드의 지각 콜백** → 무시.
- 행을 못 찾아도 자식 처리는 계속한다(완료 표시만 생략).
- 실패 콜백이면 해당 행을 `markFailed` 하고 하위 서브트리 전체를 `cascadeUnreachable` 로 종결.
- 매 콜백마다 `renewLock` 으로 5분 락을 연장한다(트리가 깊으면 필수).

---

## 6. operation 을 추가할 때

1. 이 저장소: 컨트롤러/서비스에서 `publishToKafka("NEW_OP", ...)` 호출.
2. **Backend-Core**: `@KafkaListener` 의 `switch (operation)` 에 분기 추가.
   빠뜨리면 Consumer 가 `Unknown operation` 으로 로그만 남기고 **메시지를 버린다.**
3. `payload` 스키마가 바뀌면 `ReqAddDTO` 를 양쪽에서 함께 수정.
4. 순서 의존이 있는 operation 이면 발행 순서를 명시적으로 보장한다
   (`ReqDefNodePublisher.updateAndMove` 처럼 `flatMap` 으로 직렬화).

---

## 7. 운영 확인

```bash
kafka-topics.sh --bootstrap-server <broker>:9094 --describe --topic REQADD
kafka-consumer-groups.sh --bootstrap-server <broker>:9094 --describe --group <backend-core-group>
kafka-console-consumer.sh --bootstrap-server <broker>:9094 --topic REQADD --from-beginning \
    --property print.key=true
```

Middle-Proxy 발행 로그는 `📤 Kafka Message Published | Topic: ... Partition: ... Offset: ... RequestId: ...`,
실패는 `❌ Kafka Publish Failed | RequestId: ...` 형태다. `requestId` 로 Backend-Core 로그와 대조한다.
