# aigenerate 파이프라인 · 질의 도메인 계약

`src/main/java/com/arms/egovframework/javaservice/aigenerate/` 는 **도메인이 아니라 재사용 프레임워크**다.
`api/<domain>/` 은 이 프레임워크를 조합해 각자의 답변을 만든다.

---

## 1. 7단계 파이프라인

```
UserQuery (l_)        사용자 원본 자연어 질의 — UserQueryDTO
    ↓
RAG (ll_)             VectorStore 유사 검색 — RagService
    ↓
Keyword (lll_)        주제어 추출 (LLM 2단계) — KeywordService
    ↓
SearchEngine (lv_)    Engine-Fire 키워드 검색 — SearchEngineService
    ↓
Prompt (v_)           위 셋을 PromptContextVO 로 조합 — PromptContextService
    ↓
AiRequest (vl_)       조합 컨텍스트로 LLM 호출 — AiRequestService
    ↓
AiResponse (vll_)     응답 후처리·산출물 — AiResponseService
```

**접두가 의존 방향이다.** 접두가 긴 쪽(하위 단계)이 짧은 쪽(조합 단계)을 참조하면 순환이 생긴다.
새 단계를 넣으면 접두 규칙에 맞춰 배치하고 해당 패키지의 `package-info.java` 에 적는다.

---

## 2. 단계별 계약

### 2.1 `l_query` — 진입

| 타입 | 역할 |
|------|------|
| `UserQueryDTO` (abstract) | `queryText` · `sessionId` · `language`(기본 `ko`) · `createdAt` · `metadata` · `isValid()` |
| `UserQueryService<Q>` | `Flux<String> stream(Q)` · `Mono<String> generate(Q)` · `String stopStream(String)` |
| `UserQueryAbstractController<S,Q>` | 4개 엔드포인트 + Keyword→HTML 게이트 |
| `ChatModelRouter` | `chatModel()` / `routingModel()` — 모델 배정의 유일한 출입구 |
| `UserQueryServiceImpl` | 프레임워크 기본 구현. `buildContext` · `execute` · `executeStream` 을 추가로 제공 |

`UserQueryServiceImpl` 의 기본값: `DEFAULT_TOP_K=2` · `DEFAULT_THRESHOLD=0.7` · `DEFAULT_KEYWORD_CNT=3`.

### 2.2 `ll_rag` — 검색과 RAG 응답

`RagService` 는 세 가지를 제공한다.

```java
List<RagResultVO> search(UserQueryDTO q, int topK, double threshold);  // LLM 없이 문서만
Flux<String>      ragStream(UserQueryDTO q, String streamId, int topK, double threshold);
Mono<String>      ragGenerate(UserQueryDTO q, int topK, double threshold);
```

`ragStream`/`ragGenerate` 는 `RetrievalAugmentationAdvisor` 를 매 호출마다 새로 만든다
(topK·threshold 가 호출마다 달라서다).

```java
RetrievalAugmentationAdvisor.builder()
    .documentRetriever(VectorStoreDocumentRetriever.builder()
            .vectorStore(vectorStore).topK(topK).similarityThreshold(threshold).build())
    .queryAugmenter(ContextualQueryAugmenter.builder()
            .allowEmptyContext(true)          // ★ 검색 결과가 없어도 LLM 을 부른다
            .build())
    .build();
```

`allowEmptyContext(true)` 를 빼면 검색 0건일 때 LLM 이 아예 호출되지 않고 "답변할 수 없습니다"만 나간다.
바꾸려면 의도를 명시한다.

`similaritySearch` 는 `null` 을 돌려줄 수 있다. `RagServiceImpl.search` 처럼 **항상 null 가드**를 둔다.

### 2.3 `lll_keyword` — 2단계 추출

```
[1단계] queryText            → LLM → primaryKeyword 1개 (항상 keywords[0])
[2단계] queryText + ragAnswer → LLM → 보조 키워드 (count-1)개, primary 와 중복 제거
[최종]  LinkedHashSet 으로 합쳐 순서 유지, 최대 count 개
```

- `count <= 1` 이면 2단계를 건너뛴다.
- LLM 응답 정제가 핵심이다. `sanitizeSingleWord` 는 기호를 지우고 첫 단어만 취하고,
  `parseKeywords` 는 줄 단위로 쪼갠 뒤 한글·영문·숫자만 남긴다. **모델을 바꾸면 이 정제부터 깨진다.**
- `KeywordServiceImpl` 은 `ChatModel` 을 **직접** 주입받는다(= `@Primary` `answerChatModel`).
  `ChatModelRouter` 를 거치지 않는 예외다. 손볼 일이 있으면 라우터 경유로 맞추는 쪽이 일관적이다.

### 2.4 `lv_searchengine` — Engine-Fire 위임

`EngineClient.searchByKeyword(KeywordSearchRequestDTO)` **단일 호출**로 OR 검색한다.
키워드마다 따로 부르지 않는다. 키워드가 비면 호출하지 않고 빈 목록을 돌려준다.

### 2.5 `v_prompt` — 조합 (순서 고정)

`PromptContextServiceImpl.build(queryText, keywordCount)`:

1. RAG 검색 (`RAG_TOP_K=2`, `RAG_THRESHOLD=0.7`)
2. RAG content 를 `mergeRagContents` 로 이어붙여 Keyword 입력으로 전달
3. 키워드로 SearchEngine 검색
4. `PromptContextVO(queryText, ragResults, keywords, searchDocuments)` 반환

**순서를 바꾸면 Keyword 가 RAG 결과를 못 받고, SearchEngine 이 키워드 없이 호출된다.**
총 3초를 넘으면 `[느린 요청 감지 {}ms]` 로 `WARN` 이 찍힌다 — 성능 조사 시 이 로그부터 본다.

`build` 는 블로킹이다. 호출부(`UserQueryServiceImpl.buildContext`)가
`Mono.fromCallable(...).subscribeOn(boundedElastic())` 로 감싼다.

### 2.6 `vl_airequest` — LLM 호출

`AiRequestServiceImpl.buildPrompt` 가 고정된 순서로 프롬프트를 쌓는다.

```
[사용자 질의]
[RAG 유사 문서]      - content 줄 나열
[핵심 키워드]        쉼표 구분
[검색 문서]          ▶ title 다음 content
[답변 지시]          근거 기반 · 없으면 "관련 정보를 찾을 수 없습니다" · 한국어
```

섹션은 값이 있을 때만 붙는다. **섹션 머리표 문자열을 바꾸면 모델 출력이 흔들린다** — 바꿀 이유가 있을 때만 바꾼다.

### 2.7 `vll_airesponse` — 산출물

`OutputType` 으로 응답을 문서·PPT 등으로 떨군다. PPT 스타일 관례(960x540, 제목색 `#1F3864`)는
`ReportServiceImpl.writeReportPpt` 도 따른다.

---

## 3. 새 질의 도메인 만들기 — 체크리스트

1. `api/<domain>/model/dto/<Foo>DTO.java` — `UserQueryDTO` 상속.
   **`@SuperBuilder` + `@EqualsAndHashCode(callSuper = true)` 를 빠뜨리면 빌더가 부모 필드를 못 채운다.**
2. `api/<domain>/service/<Foo>ServiceImpl.java` — `UserQueryService<FooDTO>` 구현.
   - `stream` 은 `Flux.defer` + `takeUntil` + `doFinally` 3종 세트
   - `generate` 는 `Mono.fromCallable(...).subscribeOn(boundedElastic())`
   - `stopStream` 은 플래그만 세우고 안내 문자열 반환
3. `api/<domain>/controller/<Foo>Controller.java` — `UserQueryAbstractController` 상속,
   생성자에서 `setQueryService(service)`. `@Tag` 로 Swagger 그룹명을 준다.
4. (선택) 도메인 전용 엔드포인트는 상속받은 컨트롤러에 **추가**한다
   (`MultiAgentController.parseExcel` / `exportExcel` 이 그 예다).

### 파이프라인을 얼마나 쓸지 고르기

| 원하는 것 | 쓰는 것 |
|-----------|---------|
| RAG 만으로 답변 | `RagService.ragStream` / `ragGenerate` (= 프레임워크 기본 `UserQueryServiceImpl`) |
| 7단계 전체 | `UserQueryServiceImpl.executeStream` / `execute` (= `SampleQueryServiceImpl`) |
| 직접 프롬프트를 조립 | `ChatModelRouter.chatModel()` + `ChatClient` 직접 사용 (= `ChatServiceImpl` · `SupportServiceImpl`) |
| 도구·서브에이전트 | `references/agents-and-tools.md` |

---

## 4. 스트림 청크 프로토콜 (프론트 계약)

`Flux<String>` 의 청크는 단순 텍스트만이 아니다. 도메인마다 **앞에 JSON 청크를 끼워** 보낸다.

| 도메인 | 앞머리 청크 | 의미 |
|--------|------------|------|
| `support` | `{"progress":"..."}` | 진행 상태 문구 |
| `support` | `{"screens":[{pageKey,metrics,tasks}]}` 또는 `{}` | 근거 지표 |
| `support` | `{"assigneePick":{...}}` | 담당자 지목이 필요할 때 |
| `multiagent` | `{"progress":"..."}` | 진행 상태 문구 |
| `chat` (프로젝트 분석) | 마크다운 프로젝트 정보 + 집계 JSON | 헤더 + 원자료 |

**이 모양을 바꾸면 프론트가 깨진다.** 새 청크 타입을 넣으면 프론트 변경이 함께 필요하다는 점을 명시한다.
`PmExpertAgent` 시스템 프롬프트에 `답변을 "{" 로 시작하지 않는다` 가 있는 이유도 이것이다 —
본문이 `{` 로 시작하면 프론트가 JSON 청크로 오인한다.
