---
name: ai-expert
description: >-
  A-RMS 생성·검색 AI 저장소(Java-Service-Tree-Framework-AI)의 작업 규약.
  Spring Boot 3.5.6 · Java 21 · Spring AI 1.0.0-M8 · WebFlux 기반이며
  Backend-Core(Boot 2.6 · Java 11 · MVC/JPA) · Middle-Proxy(게이트웨이) · Engine-Fire(OpenSearch 집계)와
  규칙이 전혀 다르다. AI 질의 파이프라인(aigenerate 7단계) · UserQueryAbstractController 상속 도메인 ·
  RAG/OpenSearch VectorStore · 역할별 LLM 분리(답변=Ollama, 라우팅=Anthropic) · 도구 호출(@Tool) ·
  멀티에이전트(오케스트레이터 + PM expert + req_to_task 스킬) · AI Support 화면 지표 브리핑 ·
  문서 벡터화(PDF · Markdown · JSON/NDJSON) · 프롬프트 외부화(Config Server)를 건드릴 때 반드시 먼저 읽을 것.
  ChatModelRouter · answerChatModel · FallbackChatModel · OllamaWarmupRunner · RetrievalAugmentationAdvisor ·
  VectorStoreDocumentRetriever · ContextualQueryAugmenter · OpenSearchVectorStoreConfig · chunk_type ·
  hierarchy_path · SupportRouter · SupportToolsService · PageMetricCollector · MultiAgentOrchestrator ·
  PmExpertAgent · ReqToTaskSkill · PmbokSearchTool · ToolContext · internalToolExecutionEnabled ·
  KeywordHtmlResolver · streamStatus · takeUntil · prompt.support.* · Feign(BackendCoreClient · EngineClient) ·
  "첫 토큰이 느리다" · "임베딩 모델을 바꾸고 싶다" · "도구가 호출이 안 된다" 같은 주제도 대상이다.
  "AI 모듈", "ai-expert", "챗", "RAG", "벡터스토어", "프롬프트", "서브에이전트", "AI Support" 요청도 여기서 시작한다.
  단, 같은 "AI 챗" 이라도 대화방·메시지·첨부 문서를 Redis 에 저장하는 쪽은 middleproxy-expert 이고,
  여기는 그 질의를 받아 LLM 을 부르는 쪽이다. 같은 "집계·대시보드·리포트" 라도 OpenSearch 색인·집계는
  engine-expert, MySQL 트리(nested-set) 요구사항 CRUD 는 arms-backend-core 이며,
  여기는 그 결과를 Feign 으로 받아 프롬프트에 넣는 쪽이다.
  프롬프트 문구·화면 카탈로그(prompt.support.targets) 같은 설정 "값" 자체는 config-expert 다.
  Spring MVC(HttpServletRequest · @Transactional · JPA)나 Boot 2.6 · Java 11 문법으로 작성하지 않는다 —
  이 저장소는 Boot 3.5 · Java 21 · 전부 리액티브다.
---

# A-RMS AI 모듈 작업 규약

대상 저장소: `Java-Service-Tree-Framework-AI/`
(워크스페이스 루트 `C:\DEV\Project\Java-Service-Tree-Framework` 하위, 중첩 git 저장소 · 브랜치 `dev`)

이 저장소는 A-RMS에서 **LLM 을 실제로 호출하는 유일한 모듈**이다. 임베딩·RAG·프롬프트 조합·
도구 호출·서브에이전트가 전부 여기 있다. ALM 수집·집계는 Engine-Fire, 요구사항 CRUD 는 Backend-Core 이며
이 모듈은 그 결과를 **Feign 으로 받아 쓰기만 한다**. 경계를 넘으면 같은 로직이 두 모듈로 갈라진다.

---

## 0. 30초 요약 — 반드시 먼저 각인할 것

| 항목 | 값 |
|------|----|
| 스택 | Spring Boot **3.5.6** · Spring Cloud **2025.0.1** · **Java 21** · Gradle 8.13 |
| AI | **Spring AI 1.0.0-M8** (마일스톤 — 정식판과 API 가 다르다) |
| 웹 모델 | **Spring WebFlux (리액티브)** · `@EnableWebFlux` · `@EnableScheduling` |
| 영속 | **없음.** RDB·Redis·JPA 전부 없다. 상태는 OpenSearch VectorStore 와 in-memory 맵뿐 |
| 답변 LLM | **Ollama(로컬)** — 실패 시 Anthropic 폴백 (`FallbackChatModel`) |
| 라우팅 LLM | **Anthropic(외부)** — 질문 원문만 넘기는 도구 선택 전용 |
| 임베딩 | **Ollama 고정** (`ollamaEmbeddingModel`). 바꾸면 기존 인덱스가 전부 무효 |
| 벡터 저장소 | 자체 호스팅 **OpenSearch(평문 HTTP)** — 자동구성 배제 후 수동 등록 |
| 설정·프롬프트 | 대부분 **Spring Cloud Config(Global-Config)가 주입** — 저장소 yml 은 몇 줄짜리 뼈대뿐 |
| 버전 | `26.9.x` (patch 는 Nexus 메타데이터에서 자동 증가) |

### 이 저장소에서 쓰면 안 되는 것

```
✗ HttpServletRequest / HttpServletResponse   → ✓ ServerHttpRequest / ServerWebExchange
✗ @Transactional / JPA Entity / Repository    → ✓ DB 가 없다. VectorStore 또는 Feign
✗ javax.*                                     → ✓ jakarta.*
✗ 컨트롤러에서 값 직접 반환                     → ✓ Mono<...> / Flux<...>
✗ 리액티브 체인에서 블로킹 호출                  → ✓ subscribeOn(Schedulers.boundedElastic())
✗ 시스템 프롬프트를 코드에 하드코딩              → ✓ @Value("${prompt....}")  (에이전트 페르소나는 예외 — §5)
✗ ChatModel 을 @Qualifier 없이 새로 주입         → ✓ ChatModelRouter 경유
✗ 임베딩 모델 교체                              → ✓ 금지. 인덱스 전량 재적재가 필요한 별도 과제
```

> 루트 `README.md` 는 **오래됐다** — Boot 3.4.4 · `SampleController` · `SafeGuardAdvisor` 로 적혀 있으나
> 셋 다 현재 코드와 다르다. `build.gradle` 과 소스가 언제나 정본이다.

---

## 1. 요청이 어디로 가는지 먼저 판별한다

들어온 요청은 **셋 중 하나**다. 어느 쪽인지 모르면 엉뚱한 파일을 고친다.

```
Frontend / Middle-Proxy
        │
        ├─(A) 질의 파이프라인 도메인  → UserQueryAbstractController 상속 4종
        │     /chat · /support · /anonymous/multiagent · /sample/query
        │     공통 엔드포인트: POST /stream · POST /generate · GET /stop-stream · POST /validate
        │
        ├─(B) 적재·검색·부가 API      → 독립 @RestController
        │     /ai/markdown · /pdf · /admin/vector · /admin/vector/ndjson · /admin/filesystem
        │     /ai/search · /evaluation · /report · /performance · /tool-calling · /tts
        │
        └─(C) 상태 조회               → /chat/status · /anonymous/chat/status · /status
```

### (A) 질의 파이프라인 도메인 지도 (실제 `@RequestMapping` 기준)

| 도메인 | 경로 | 서비스 | 하는 일 |
|--------|------|--------|---------|
| `chat` | `/chat` | `ChatServiceImpl` | 일반 챗 + `pdServiceId` 가 있으면 Engine-Fire 집계를 붙인 "프로젝트 분석" |
| `support` | `/support` | `SupportServiceImpl` | AI Support — 화면 지표 브리핑 · 자유 입력 라우팅(도구 21종) |
| `multiagent` | `/anonymous/multiagent` | `MultiAgentServiceImpl` | 오케스트레이터 → PM expert 서브에이전트 (요구사항 → 착수 지시서) |
| `sample` | `/sample/query` | `SampleQueryServiceImpl` | aigenerate 7단계 파이프라인 **레퍼런스 구현**. 새 도메인은 여기를 베낀다 |

> `/anonymous/**` 접두는 MABC 대회 시연용으로 인증을 뺀 임시 경로다
> (`AiStatusController.statusForMABC` 에 `TODO: 대회 이후 소스코드 원복 필요` 가 붙어 있다).
> 새 도메인에 `/anonymous` 를 따라 붙이지 않는다.

---

## 2. 계층 구조 — 패키지가 규칙이다

```
com.arms
├─ Application.java        @EnableWebFlux · @EnableScheduling
│                          + OpenSearchVectorStoreAutoConfiguration 배제 (§6.1 — 지우면 기동 실패)
├─ config/                 LlmModelConfig · FallbackChatModel · OllamaWarmupRunner
│                          OpenSearchVectorStoreConfig · OpenFeignConfig · OpenApiConfig · RestClientConfig
├─ api/<domain>/           controller / service / model{dto,vo} — 비즈니스 도메인
│  └─ util/                advisors · error · keyword · msa_communicator(Feign) · response · status
└─ egovframework.javaservice.aigenerate/   ★ 재사용 프레임워크 계층 (도메인 아님)
```

### aigenerate 레이어 접두 — 의존 방향이 이름에 박혀 있다

| 접두 | 패키지 | 단계 |
|------|--------|------|
| `l_` | `l_query` | 사용자 원본 질의 · 추상 컨트롤러 · `ChatModelRouter` |
| `ll_` | `ll_rag` | VectorStore 유사 검색 · RAG advisor |
| `lll_` | `lll_keyword` | 주제어 추출 (LLM 2단계) |
| `lv_` | `lv_searchengine` | Engine-Fire 키워드 검색 |
| `v_` | `v_prompt` | RAG → Keyword → SearchEngine 조합 (`PromptContextVO`) |
| `vl_` | `vl_airequest` | 조합된 컨텍스트로 LLM 호출 |
| `vll_` | `vll_airesponse` | 응답 후처리·산출물(문서/PPT) |

**상위(조합) → 하위 방향만 허용한다.** `ll_rag` 가 `v_prompt` 를 참조하면 안 된다.
새 단계를 넣으면 접두 규칙에 맞춰 배치하고 `package-info.java` 에 적는다.

상세: `references/pipeline.md`

---

## 3. 새 질의 도메인 만들기 — 3파일이면 끝난다

`sample` 패키지가 정본 레퍼런스다. 그대로 베껴 쓴다.

```java
// ① DTO — UserQueryDTO 를 상속. @SuperBuilder + @EqualsAndHashCode(callSuper = true) 필수
@Getter @SuperBuilder @NoArgsConstructor @EqualsAndHashCode(callSuper = true)
public class FooDTO extends UserQueryDTO {
    private Long pdServiceId;          // 도메인 확장 필드
}

// ② Service — UserQueryService<Q> 구현. stream / generate / stopStream 3개
@Slf4j @Service @RequiredArgsConstructor
public class FooServiceImpl implements UserQueryService<FooDTO> { ... }

// ③ Controller — 상속만 하면 /stream · /generate · /stop-stream · /validate 가 생긴다
@RestController @RequestMapping("/foo")
public class FooController extends UserQueryAbstractController<FooServiceImpl, FooDTO> {
    @Autowired public FooController(FooServiceImpl service) { setQueryService(service); }
}
```

`assets/query-domain-template/` 에 뼈대가 있다.

### 추상 컨트롤러가 이미 해 주는 것 (다시 만들지 말 것)

- `POST /{base}/stream` — `text/event-stream`, `Flux<String>`
- `POST /{base}/generate` — 단건. 에러 시 500 + 한국어 메시지
- `GET  /{base}/stop-stream?sessionId=` — 스트림 중단
- `POST /{base}/validate` — LLM 호출 없이 유효성만
- **Keyword→HTML 게이트** — `chat.keyword-html.mappings` 에 걸리면 **LLM 을 아예 안 부르고**
  매핑된 HTML 을 120자 / 30ms SSE 청크로 흘린다. `KeywordHtmlResolver` 빈이 없으면 게이트는 꺼진다.

> ⚠️ "AI가 멈춘 것처럼 보인다"는 신고의 상당수가 이 게이트다. 코드 버그가 아니다.
> `chat.keyword-html.enabled: false` 또는 매핑 조정으로 푼다.

---

## 4. LLM — 모델 배정은 정책이지 설정이 아니다

```
ChatModelRouter
 ├─ chatModel()    = @Primary "answerChatModel"     → 고객 데이터를 보는 모든 호출
 │                    기본: FallbackChatModel(Ollama → Anthropic)
 │                    spring.ai.answer.external-chat=true 면 OpenAI 호환(Upstage Solar) 고정
 └─ routingModel() = "anthropicChatModel"           → 질문 원문만 넘기는 도구 선택 전용
```

**가르는 기준은 "모델이 고객 데이터를 보느냐"** 다. 지표·문서·요구사항 원문이 프롬프트에 들어가면
반드시 `chatModel()` 을 쓴다. `routingModel()` 은 **질문 원문만** 넘기는 곳에만 쓴다 — 현재
`SupportRouter` 와 `MultiAgentOrchestrator` 둘뿐이다.

- 이 배정을 설정 키로 빼지 않는다. 값 하나 잘못 넣으면 고객 데이터가 외부로 나간다.
- `ChatModel` 을 `@Qualifier` 없이 새로 주입하면 `@Primary` 인 `answerChatModel` 이 들어온다.
  의도한 게 아니면 `ChatModelRouter` 를 주입한다.
- `FallbackChatModel` 은 **스트리밍 도중 실패하면 전환하지 않는다**(첫 청크가 나간 뒤에는 폴백 금지).
  중복 출력을 막기 위한 의도된 동작이다.
- 폴백 프롬프트는 `new Prompt(prompt.getInstructions())` 로 **옵션을 버리고** 넘긴다.
  Ollama 전용 옵션이 Anthropic 에서 400 을 내기 때문이다.

### Cold start 예열

`OllamaWarmupRunner` 가 기동 직후 데몬 스레드로 chat/embedding 을 한 번씩 부른다.
상태는 `GET /chat/status` (`chat` · `embedding` · `chatFallback` · `ready`).
**`ready=true` 전의 느린 첫 토큰은 버그가 아니다.** 예열 로직을 임의로 지우지 않는다.

상세: `references/llm-and-models.md`

---

## 5. 프롬프트 — 외부화가 기본, 페르소나는 예외

| 종류 | 위치 | 예 |
|------|------|-----|
| 시스템 메시지 | **Config Server** `@Value("${prompt....}")` | `prompt.support.{role,planner,synthesis,common,lens-project,lens-settings}` · `prompt.chat-stream.system-message` · `prompt.project-analysis.system-message` · `prompt.kpi-report.system-message` · `prompt.performance-{generate,news}.system-message` |
| 화면 카탈로그 | **Config Server** `@ConfigurationProperties("prompt.support")` | `targets[].{id,title,description,knowledgeArea}` |
| 에이전트 페르소나 | **코드 상수** (`private static final String SYSTEM_PROMPT`) | `MultiAgentOrchestrator` · `PmExpertAgent` |
| 스킬 지시서 | **코드 상수 + `@Tool` 반환값** | `ReqToTaskSkill.INSTRUCTIONS` |
| 보조 프롬프트 | 코드 상수 | `KeywordServiceImpl` 1·2단계 템플릿 |

새 시스템 메시지는 **기본값 없는** `@Value("${prompt.x.y}")` 로 넣는다. 기본값을 주면 Config Server 에
키가 없어도 조용히 기동해서, 운영에서 빈 프롬프트로 도는 것을 못 잡는다.

> 프롬프트 값을 바꿔야 하면 이 저장소가 아니라 **Global-Config(Gitea)** 를 고쳐야 한다는 점을 사용자에게 명시한다.

---

## 6. RAG · VectorStore

### 6.1 수동 구성인 이유 (지우면 기동이 깨진다)

`bedrock-converse` 스타터 때문에 AWS SDK 가 클래스패스에 상주 → M8 자동구성이 `AwsSdk2Transport`(HTTPS 강제)를
선택 → 평문 HTTP OpenSearch 에 접속하면 `SSLException` 으로 기동 실패.
그래서 `Application` 이 `OpenSearchVectorStoreAutoConfiguration` 을 **exclude** 하고
`OpenSearchVectorStoreConfig` 가 ApacheHttpClient5 트랜스포트로 직접 등록한다. **둘 다 건드리지 않는다.**

### 6.2 검색 파라미터 — 호출부마다 다르고, 다 이유가 있다

| 호출부 | topK | threshold | filter |
|--------|------|-----------|--------|
| `RagServiceImpl` 상수 기본값 | 5 | 0.7 | 없음 |
| `UserQueryServiceImpl` · `PromptContextServiceImpl` | 2 | 0.7 | 없음 |
| `ChatServiceImpl` (PMBOK) | 2 | 0.7 | 없음 |
| `SupportServiceImpl` (근거 1건) | 1 | 0.5 | `chunk_type == 'content'` |
| `PmbokSearchTool` (근거 3건) | 3 | 0.5 | `chunk_type == 'content'` |
| `EvaluationServiceImpl` | 3 | 0.7 | 없음 |

`summary` 청크는 요약이라 **근거로 인용하기에 부족하다** — 그래서 근거 검색은 `chunk_type == 'content'` 로 거른다.

### 6.3 문서 메타데이터 스키마 (`MarkdownChunkMetadataVO.toMap()` 이 정본)

`source` · `file_name` · `page_number` · `chapter` · `chapter_title` · `section` · `section_title` ·
`process_group[]` · `knowledge_area[]` · `keywords[]` · **`chunk_type`**(`content`|`summary`) ·
**`hierarchy_path`** · `has_diagram` · `diagram_title`

키를 늘리면 기존 색인 문서에는 그 키가 없다. **필터에 쓸 키는 재적재 없이 추가하지 않는다.**

### 6.4 적재 경로 4종

| 경로 | 엔드포인트 | 청킹 |
|------|-----------|------|
| Markdown | `POST /ai/markdown/vectorize` | 파일당 최대 2청크(content + summary) + 계층·분류·키워드 텍스트 보강 |
| PDF | `POST /pdf/vectorize` | Paragraph/Page Reader + 이미지 설명(멀티모달) + `TokenTextSplitter` |
| JSON | `POST /admin/vector`, `/admin/vector/auto-classify` | 필드 역할 분류(CONTENT/CONTENT_COMPONENT/METADATA) 후 2-pass 스트리밍 |
| NDJSON | `POST /admin/vector/ndjson` | 위와 동일 계열 |

`VectorStoreRepository.deleteByPath(path)` → `save(documents)` 가 **재적재의 정본 순서**다.
지우지 않고 저장하면 중복 문서가 쌓이고 검색 품질이 떨어진다.

상세: `references/rag-and-vectorstore.md`

---

## 7. 도구 호출 · 서브에이전트

이 저장소에는 `@Tool` 사용 패턴이 **세 가지**다. 섞지 않는다.

### 7.1 계획만 시키고 실행은 내가 한다 (Support)

```java
ToolCallingChatOptions.builder()
        .toolCallbacks(tools)
        .internalToolExecutionEnabled(false)   // ★ 도구 결과가 모델로 안 돌아간다
        .build();
```

모델은 **어느 화면을 볼지 이름만 고르고**(최대 2개), 실제 수집은 `SupportServiceImpl` 이
`ToolCallback.call("{}", toolContext)` 로 직접 돌린다. 지표(고객 데이터)가 라우팅 모델에 안 들어간다.

- **도구 이름 = pageKey = collector 의 `PAGE_KEY`** 3자를 반드시 맞춘다.
- 조회 조건(제품·버전·담당자)은 `ToolContext` 로 넘긴다. `ToolContext` 파라미터는 스키마에서 제외되어
  모델에 노출되지 않는다. **화면을 인자로 받지 않는다.**
- 새 화면을 붙이려면 ① `PageMetricCollector` 구현체 ② `SupportToolsService` 의 `@Tool` 메서드
  ③ Config Server `prompt.support.targets[]` — **셋 다** 필요하다.

### 7.2 서브에이전트에게 넘긴다 (MultiAgent)

```
사용자 입력
  → MultiAgentOrchestrator (routingModel · internalToolExecutionEnabled=false · timeout 20s)
      ├─ pm_expert 툴콜 →  PmExpertAgent (chatModel · 도구를 실제로 실행)
      │                      ├─ req_to_task (ReqToTaskSkill — 지시서 텍스트를 반환하는 "스킬")
      │                      └─ pmbok_search (PmbokSearchTool — VectorStore 근거 검색)
      └─ 툴콜 없음 → 오케스트레이터가 직접 답변
```

- 오케스트레이터에는 **첨부 사실만**, PM expert 에는 **첨부 행 원문까지** 넘긴다
  (`ReqSheetPromptComposer.routingText` vs `agentText`). 외부 모델에 고객 데이터를 주지 않는다.
- 진행 상태는 `{"progress":"..."}` JSON 청크를 스트림 앞에 끼워 보낸다. 프론트가 이 모양에 의존한다.
- **스킬 패턴**: `@Tool` 이 실행 결과가 아니라 **방법론 텍스트**를 돌려주고, 에이전트가 그 절차를 따른다.
  시스템 프롬프트를 늘리지 않고 역량을 붙이는 방식이다.

### 7.3 그냥 도구를 실행시킨다 (toolcalling)

`ChatClient.builder(chatModel).defaultTools(toolsService)` — Spring AI 기본 동작. 데모성 코드다.

상세: `references/agents-and-tools.md`

---

## 8. 리액티브 규칙

### 8.1 블로킹은 전부 격리한다

`VectorStore.similaritySearch` · `ChatClient...call()` · Feign · POI · 파일 IO 는 **전부 블로킹**이다.

| 상황 | 감싸는 법 |
|------|----------|
| 값을 반환 | `Mono.fromCallable(() -> ...).subscribeOn(Schedulers.boundedElastic())` |
| 이미 `Mono` 를 받았고 이후가 블로킹 | `.publishOn(Schedulers.boundedElastic())` (`ReqSheetService` 패턴) |
| 스트리밍(`ChatClient...stream()`) | Spring AI 가 비동기로 돌려주므로 추가 격리 불필요 |

### 8.2 스트림 중단·정리는 정해진 모양이 있다

```java
private final ConcurrentHashMap<String, AtomicBoolean> streamStatus = new ConcurrentHashMap<>();

return Flux.defer(() -> {
            streamStatus.put(streamId, new AtomicBoolean(false));
            return chatClient.prompt()/* ... */.stream().content()
                    .takeUntil(c -> streamStatus.getOrDefault(streamId, new AtomicBoolean(false)).get());
        })
        .doFinally(sig -> streamStatus.remove(streamId));   // ★ 모든 종료 경로에서 제거
```

`doFinally` 를 쓰면 취소·에러·완료가 한 번에 정리된다. `doOnComplete`/`doOnError` 만 쓰면
**클라이언트가 끊은 경우 맵에 남아 누수된다**(`RagServiceImpl` · `AiRequestServiceImpl` · `ChatServiceImpl`
이 옛 방식이다 — 새 코드는 `SupportServiceImpl` · `MultiAgentServiceImpl` 처럼 `doFinally` 를 쓴다).

`stopStream(sessionId)` 은 플래그만 세운다. 세션이 없으면 예외가 아니라 안내 문자열을 돌려준다.

---

## 9. 외부 통신 (Feign)

| 인터페이스 | 대상 | URL 키 | 쓰임 |
|-----------|------|--------|------|
| `BackendCoreClient` | Backend-Core | `${arms.backend.url}` | 요구사항·제품·버전·위키·담당자·리포트 원천 데이터 |
| `EngineClient` | Engine-Fire | `${arms.engine.url}` | 키워드 검색(`/ai-search/keyword`) · 롤링3개월 집계 · KPI 대시보드 5종 |
| `DwrClient` | Backend-Core | `${arms.backend.url}` | 진행 상황 푸시 알림 (`/arms/alarm/send-message`) |
| `TtsClient` | TTS 엔진 | `${spring.ai.tts.base-url,...}` | 현재 `TtsClientDummyImpl` 로 더미 처리 |

- `OpenFeignConfig` 가 `@EnableFeignClients({"com.arms.api.util.msa_communicator"})` 로 **그 패키지만** 스캔한다.
  다른 곳에 Feign 인터페이스를 두면 빈이 안 생긴다.
- 타임아웃 connect 30초 / read **60분**. LLM·PPT 생성이 오래 걸려서다. 줄일 때는 이유를 확인한다.
- WebFlux 라 `HttpMessageConverters` 가 자동 구성되지 않는다. `OpenFeignConfig` 가
  `MappingJackson2HttpMessageConverter` 를 수동 등록한다 — 지우면 `@RequestBody` Feign 호출이 런타임에 깨진다.
- 응답 VO(`BackendCore*VO` · `SearchEngineDocumentVO`)는 상대 모듈의 응답과 **1:1로 유지**한다.
  한쪽만 바꾸면 조용히 역직렬화가 비고, 지표가 0 으로 나온다.

상세: `references/integration-and-ops.md`

---

## 10. 실행해서 확인하기

```bash
# 컴파일만 (가장 빠른 검증)
./gradlew compileJava            # Windows: gradlew.bat compileJava
```

- **`./gradlew build` 는 오프라인에서 실패할 수 있다.** `build.gradle` 이 구성 단계에서 Nexus
  `metadata.xml` 을 읽어 patch 버전을 계산한다(Windows/Mac 은 동봉 `metadata.xml` 을 쓴다).
- **테스트 소스가 하나도 없다**(`src/test` 자체가 없다). 새 로직은 스프링 컨텍스트 없는
  순수 단위 테스트로 검증하고, 테스트를 새로 만들 때 JUnit5 + Reactor Test 를 쓴다.
- 로컬 기동: 프로파일 `dev` → Config Server `http://www.313.co.kr:33133` 에서 설정을 받는다.
  **Config Server 가 안 붙으면 `prompt.*` · `spring.ai.*` 키가 없어 기동에 실패한다.**
- Swagger: `/swagger-ui.html` (`use-root-path: true`), API 문서 `/v3/api-docs`
- Actuator(dev): `/actuator/{refresh,env,health,beans,httptrace}`

---

## 11. 제출 전 자가 점검

- [ ] 컨트롤러가 `Mono`/`Flux` 를 반환하는가? Servlet·JPA 타입을 쓰지 않았는가?
- [ ] 블로킹 호출(VectorStore · `ChatClient...call()` · Feign · POI)을 `boundedElastic` 으로 격리했는가?
- [ ] 스트림을 만들었다면 `takeUntil` + `doFinally` 로 `streamStatus` 를 정리하는가?
- [ ] 고객 데이터가 들어가는 프롬프트에 `chatModelRouter.chatModel()` 을 썼는가?
      `routingModel()` 에 질문 원문 말고 다른 걸 넘기지 않았는가?
- [ ] 새 시스템 프롬프트를 코드에 하드코딩하지 않고 `@Value("${prompt....}")` 로 뺐는가?
      (Global-Config 변경이 필요하다는 점을 보고했는가?)
- [ ] 임베딩 모델·VectorStore 자동구성 배제·`OpenSearchVectorStoreConfig` 를 건드리지 않았는가?
- [ ] 메타데이터 키를 늘렸다면 재적재가 필요하다는 점을 명시했는가?
- [ ] 새 Support 화면이면 collector · `@Tool` · `prompt.support.targets[]` **셋 다** 반영했는가?
      도구 이름 = pageKey = `PAGE_KEY` 가 일치하는가?
- [ ] aigenerate 레이어 접두 의존 방향(상위→하위)을 어기지 않았는가?
- [ ] Feign VO 를 바꿨다면 상대 모듈(Backend-Core · Engine-Fire) 동반 변경을 명시했는가?
- [ ] Boot 3.5 / Java 21 / `jakarta.*` 만 썼는가?
- [ ] 시크릿(Sonar 자격증명 · API 키 · Nexus 계정)을 코드·로그·문서에 복제하지 않았는가?

---

## 12. 산출 및 인계

- 사용자 대상 설명은 **한국어**로 한다.
- **commit·push 하지 않는다.** 작업 요약과 커밋 메시지 초안만 제시하고 커밋은 사용자가 한다.
  이 저장소의 실제 컨벤션(YouTrack 연동):
  ```
  feat : [ARMS-1080] #comment 생성 LLM 을 역할별로 분리 — 답변=Ollama, 라우팅=Anthropic
  feat : [ARMS-1199] #comment MABC 대회 시연 코드 ( 멀티 에이전트 시스템 )
  fix  : [ARMS-1182] #comment AiSupport Bedrock 실패 시 Anthropic fallback
  ```
  작업 브랜치는 `dev` 다(`main` 아님). 루트 워크스페이스와 별개의 중첩 git 저장소다.
- 확신이 없는 지점(Config Server 의 실제 프롬프트 값, Ollama 모델명, OpenSearch 인덱스 상태,
  다운스트림 응답 스펙)은 추측으로 메우지 말고 **가정을 명시**한다.

---

## 13. 참조 파일 지도

| 파일 | 언제 읽나 |
|------|----------|
| `references/pipeline.md` | aigenerate 7단계·새 질의 도메인·컨트롤러/서비스 계약을 다룰 때 |
| `references/llm-and-models.md` | 모델 배정·폴백·예열·프롬프트 외부화를 건드릴 때 |
| `references/rag-and-vectorstore.md` | 검색 파라미터·메타데이터·청킹·적재 경로를 다룰 때 |
| `references/agents-and-tools.md` | `@Tool` · Support 라우팅 · 멀티에이전트 · 스킬 패턴 작업 시 |
| `references/domains.md` | 특정 도메인(chat · support · multiagent · report · performance · evaluation · 적재 · filesystem · tts) 작업 시 |
| `references/integration-and-ops.md` | Feign · Config Server · 빌드 · Docker · Nexus · Swagger · 모니터링 |
| `references/pitfalls.md` | 이상 동작이 보일 때 / 착수 전 함정 확인 |
| `assets/query-domain-template/` | 새 질의 도메인 뼈대 (DTO · Service · Controller) |

저장소 자체 문서 `Java-Service-Tree-Framework-AI/docs/ai/` 도 보조 정본이다
(`harness_engineering.md` 가 지도, `12_known_issues/guide.md` 에 함정 누적,
`06_domain_playbooks/` 에 rag · user-query · prompt-pipeline · llm-provider · ai-search).
**단, 일부가 코드보다 뒤처져 있다** — `06_domain_playbooks/llm-provider.md` 와 `12_known_issues` 의
Bedrock 서술은 현재 `LlmModelConfig`(Ollama → Anthropic 폴백, 외부 전환 시 OpenAI)와 다르다.
**코드가 정본이다.** 작업 후 변경은 `11_changelog`, 새 함정은 `12_known_issues` 에 남긴다.

> 현재 상태가 애매해 손대기 전에 확인이 필요한 것: 루트 `README.md`(코드와 불일치),
> `AI-FRAMEWORK.md`(기술 선택 메모), `docs/ai/**/engine-fire-*.md` 와 `docs/ai/06_page_playbooks/`(폐기 대상).
> 삭제는 사용자 몫이다.
