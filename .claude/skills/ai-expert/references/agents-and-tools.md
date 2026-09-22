# 도구 호출(@Tool) · 서브에이전트 · 스킬

이 저장소에는 `@Tool` 사용 패턴이 **세 가지**다. 목적이 달라서 섞으면 안 된다.

| 패턴 | 누가 | 모델이 도구를 실행하나 | 고객 데이터가 모델에 가나 |
|------|------|----------------------|-------------------------|
| ① 계획만 시킨다 | `SupportRouter` | ✗ (`internalToolExecutionEnabled(false)`) | ✗ 라우팅 모델엔 질문만 |
| ② 서브에이전트에 위임 | `MultiAgentOrchestrator` → `PmExpertAgent` | 오케스트레이터 ✗ / 에이전트 ✓ | 에이전트(로컬 모델)에만 |
| ③ 그냥 실행 | `ToolCallingServiceImpl` | ✓ (Spring AI 기본) | ✓ |

---

## 1. 패턴 ① — AI Support 화면 라우팅

### 1.1 전체 흐름

```
POST /support/stream  {queryText, sessionId, pageKey?, pdServiceId, pdServiceVersionIds, ...}
   │
   ├─ pageKey 가 있다 (화면에서 눌러 들어옴)
   │    → collector 1개로 지표 수집 + (knowledgeArea 있으면) PMBOK 근거 1건
   │    → evidence JSON 청크 → 브리핑 스트리밍
   │
   └─ pageKey 가 없다 (자유 입력)
        → {"progress":"질문을 이해하고 있어요"}
        → SupportRouter.route(queryText)          ← 라우팅 모델, 20초 타임아웃
             ├─ 텍스트만 돌아옴  → {} + 그 답변을 그대로 내보냄
             └─ 툴콜 돌아옴     → pageKey 목록 (최대 2개, MAX_SCREENS)
                  → detail_dashboard 가 섞였고 assigneeEmail 이 없으면
                       SupportAssigneeResolver 로 담당자 해석
                         ├─ 1명 확정 → 계속
                         └─ 모호/없음 → {"assigneePick":{...}} 내보내고 종료
                  → {"progress":"... 도구를 호출했어요"} / {"progress":"... 화면을 열어보고 있어요"}
                  → ToolCallback.call("{}", toolContext) 를 concatMap 으로 순차 실행
                  → {"progress":"지표 N개를 확인했어요"} / {"progress":"답변을 작성하고 있어요"}
                  → {"screens":[...]} evidence 청크
                  → prompt.support.synthesis 로 종합 답변 스트리밍
```

### 1.2 3자 일치 규칙

**도구 이름 = pageKey = collector 의 `PAGE_KEY`**

```java
// SupportToolsService
@Tool(name = "reqAdd", description = "요구 관리 — ...")
public Map<String,Object> reqAdd(ToolContext ctx) { return collect("reqAdd", ctx); }

// ReqAddMetricCollector
private static final String PAGE_KEY = "reqAdd";
public boolean supports(String pageKey) { return PAGE_KEY.equals(pageKey); }
```

이름이 어긋나면 `SupportRouter.plannedIds` 가 "알 수 없는 도구" 로 버리거나
`collect()` 가 "collector 없음" 으로 빈 Map 을 돌려준다. **둘 다 예외 없이 조용히 실패한다.**

### 1.3 `ToolContext` 로 조회 조건을 넣는다

```java
ToolContext toolContext = new ToolContext(Map.of(
        SupportToolsService.CONTEXT_KEY,      // "pageMetricContext"
        buildMetricContext(query)));          // PageMetricContextVO
```

`ToolContext` 파라미터는 **도구 스키마 생성에서 제외**되어 모델에 노출되지 않는다.
그래서 도구가 인자를 받지 않고(`call("{}", ctx)`), 모델은 제품 ID·버전·담당자를 모른다.
`resolveContext` 는 컨텍스트가 없으면 `IllegalStateException` 을 던진다 — 조용한 오작동보다 낫다.

### 1.4 새 화면 추가 체크리스트

1. `api/support/model/vo/<Foo>MetricsVO.java` — 지표 VO
2. `api/support/service/collector/<Foo>MetricCollector.java`
   - `PAGE_KEY` 상수, `supports()`, `collect()` → `Mono.fromCallable(...).subscribeOn(boundedElastic())`
   - 원천 조회 실패는 `PageMetricSupport.anyFailed(...)` 로 판단하고 **빈 VO** 를 돌려준다(예외 전파 금지)
   - 값은 `PageMetricSupport.metricVal(값, 단위, 강조, 라벨)` 로 감싼다
3. `SupportToolsService` 에 `@Tool` 메서드 한 줄 (`collect("<pageKey>", toolContext)`)
4. **Config Server** `prompt.support.targets[]` 에 `{id,title,description,knowledgeArea}` 추가
   - `title` 은 `상위 > 하위` 형태. 진행 문구에 마지막 세그먼트만 쓴다(`lastSegment`)
   - 이걸 빼면 진행 문구에 pageKey 원문이 그대로 노출된다

> 현재 `@Tool` 은 21개, 그중 `detail_dashboard` 는 담당자 컨텍스트가 필요해 특별 취급된다.
> `SupportToolsService` 주석은 "20개 노출 / reqStatusCalendar·detail_dashboard 제외"라고 적혀 있으나
> 실제 코드는 `detail_dashboard` 를 노출한다(담당자 해석 로직이 나중에 붙었다). **코드가 정본이다.**

### 1.5 evidence 청크 모양

```json
{"screens":[{"pageKey":"reqAdd","metrics":{...},"tasks":{...}}]}
```
지표가 하나도 없으면 `{}` 를 보낸다. 프론트가 이 두 모양을 구분한다.

---

## 2. 패턴 ② — 멀티에이전트 (PM 어시스턴트)

### 2.1 역할 분담

| 구성요소 | 모델 | 보는 것 | 하는 일 |
|---------|------|--------|---------|
| `MultiAgentOrchestrator` | routing (외부) | 질문 + 첨부 **파일명·건수** | `pm_expert` 를 부를지 직접 답할지 고른다 |
| `PmExpertAgent` | chat (로컬) | 질문 + 첨부 **행 원문** | 실제 답변 작성, 도구 2개 실행 |
| `ReqToTaskSkill` | — | — | `@Tool` 이 **방법론 지시서 텍스트**를 반환 |
| `PmbokSearchTool` | — | — | VectorStore 근거 검색(topK 3, threshold 0.5, content 청크만) |

### 2.2 오케스트레이터가 직접 실행하지 않는 이유

```java
.tools(subAgentTools)
.toolContext(Map.of(MultiAgentSubAgentTools.USER_TEXT, userText))
.options(ToolCallingChatOptions.builder().internalToolExecutionEnabled(false).build())
```

`internalToolExecutionEnabled(false)` 라 툴콜은 **의도 표명**으로만 쓰인다.
`parse()` 가 툴콜 이름을 보고 `Decision.delegated(...)` 로 바꾸고,
실제 실행은 `MultiAgentServiceImpl` 이 `pmExpertAgent.stream(task, agentText)` 로 한다.
이래야 **스트리밍**이 된다 — 내부 실행이면 결과가 다 모일 때까지 기다려야 한다.

> `MultiAgentSubAgentTools.pmExpert(...)` 메서드 본문은 `internalToolExecutionEnabled(false)` 때문에
> 이 경로에서는 호출되지 않는다. 도구 **정의**(이름·설명·파라미터 스키마)를 만들기 위한 껍데기다.
> 지우면 모델이 도구를 못 본다.

### 2.3 첨부 파일 흐름

```
프론트 📎
  → POST /anonymous/multiagent/excel/parse?fileName=...  (본문: 원본 바이트, octet-stream)
       ReqSheetReader → ReqSheetVO {headers, rows, sheetName, sheetNames, totalRows, parsed, reason}
  → 프론트가 MultiAgentDTO.attachment 에 실어 /stream 으로 보냄
  → ReqSheetPromptComposer 가 두 갈래로 나눔
       routingText : queryText + "[첨부 파일] 이름 · 시트 · 총 N건"
       agentText   : 위 + "[첨부 행]" + "--- n번째 행 ---" + "컬럼명: 값" 전개
  → 변환 후 [엑셀로 받기] → POST /anonymous/multiagent/excel/export → xlsx(실패 시 CSV UTF-8 BOM)
```

- **서버는 파일을 보관하지 않는다.** 요청 본문을 메모리에서 읽고 버린다. 상한 5MB
  (`PARSE_MAX_BYTES` · `EXPORT_MAX_BYTES`, 프론트 `AS_UPLOAD_MAX_BYTES` 와 같은 값).
- 본문은 코덱 집계 한도(256KB)를 피하려고 `Flux<DataBuffer>` 로 받아 `DataBufferUtils.join` 에서 상한을 건다.
  `@RequestBody` DTO 로 바꾸면 큰 파일이 깨진다.
- `transferScope` 가 목록만이면(6건 이상) 상세를 안 넘기고 "전체/ID 지정" 을 되묻는다.
- 행 경계를 `--- n번째 행 ---` 로 **서버가 확정해서** 넘긴다. 셀 안 줄바꿈 때문에 모델이 행을 잘못 세는 것을 막는다.

### 2.4 역할 인식 표 (`ReqSheetRoles`)

컬럼명은 조직마다 달라서 **이름이 아니라 역할로 매칭**한다.

- 컬럼 역할: 공백 제거 후 **정확 일치** — `요구사항` 과 `요구사항 ID` 가 섞이지 않게
- 블록 역할: **포함 일치**, 그래서 **검사 순서가 중요하다**.
  `ACCEPTANCE → CONSTRAINT → BACKGROUND → SCOPE` 순서여야
  `비기능 요구사항`(제약)이 `기능`(작업 범위)보다 먼저 걸린다. **순서를 바꾸면 분류가 뒤집힌다.**
- 헤더 판정: 역할이 2종 이상 잡히고 그중 `NAME` 또는 `CONTENT` 가 있어야 요구사항 헤더로 본다.

`ReqSheetRoles` 의 표는 `ReqToTaskSkill` STEP 1 표와 **같은 내용을 두 곳에 적은 것**이다.
한쪽만 고치면 파서와 모델이 다르게 본다. 반드시 같이 고친다.

### 2.5 스킬 패턴 — 도구가 지시서를 돌려준다

```java
@Tool(name = "req_to_task", description = "...변환하는 절차를 돌려준다...")
public String reqToTask() { return INSTRUCTIONS; }   // 실행 결과가 아니라 방법론 텍스트
```

에이전트 시스템 프롬프트에 `반드시 req_to_task 스킬을 먼저 호출하고, 돌려받은 절차와 출력 형식을
그대로 따른다. 스킬 없이 변환하지 않는다` 가 박혀 있다.

**장점**: 시스템 프롬프트가 짧게 유지되고, 변환 규칙을 한 파일에서 관리한다.
**주의**: 모델이 도구를 안 부르면 규칙이 통째로 빠진다. `PmExpertAgent` 는 `.tools(reqToTaskSkill, pmbokSearchTool)` 로
**내부 실행을 켠 채**(기본값) 붙여서 실제로 호출되게 한다.

---

## 3. 패턴 ③ — 일반 도구 실행 (`/tool-calling`)

`ChatClient.builder(chatModel).defaultTools(toolsService)` — Spring AI 기본 툴콜 루프.
`ToolsService` 는 wttr.in 날씨 조회 데모다. 프로덕션 경로가 아니다.
`returnDirect = true` 예시가 여기 있다(도구 결과를 LLM 후처리 없이 바로 반환).

---

## 4. 도구를 새로 만들 때 공통 규칙

- `@Tool(name=...)` 의 **name 을 상수로 빼고** 그 상수로 비교한다
  (`MultiAgentSubAgentTools.PM_EXPERT` · `PmbokSearchTool.NAME` · `ReqToTaskSkill.NAME`).
  문자열 리터럴을 두 군데 쓰면 오타가 조용히 통과한다.
- `description` 은 **언제 쓰는지**를 쓴다. 무엇인지가 아니라. 모델은 이걸로만 고른다.
- 도구는 **예외를 던지지 않는다.** 실패는 `"검색 실패"` · `"검색 결과 없음"` · 빈 `Map` 같은
  **값**으로 돌려준다. 예외는 툴콜 루프를 통째로 깬다.
- 반환 문자열이 길면 모델 컨텍스트를 먹는다. `PmbokSearchTool` 이 topK 3 으로 묶어 두는 이유다.
- 도구 이름을 답변에 노출하지 않도록 시스템 프롬프트에 명시한다
  (`에이전트·스킬·도구 이름(pm_expert, req_to_task 등)을 답변에 쓰지 않는다`).
