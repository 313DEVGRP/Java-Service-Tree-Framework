# LLM 모델 배정 · 폴백 · 예열 · 프롬프트 외부화

---

## 1. 빈 구성 전체 지도

클래스패스에 스타터가 4개 있어 `ChatModel` 빈이 여러 개 존재한다.

| 스타터 | 만드는 빈 | 이 저장소에서의 쓰임 |
|--------|----------|---------------------|
| `spring-ai-starter-model-ollama` | `ollamaChatModel` · `ollamaEmbeddingModel` | **답변 기본** · **임베딩 유일** |
| `spring-ai-starter-model-anthropic` | `anthropicChatModel` | **라우팅 전용** + 답변 폴백 |
| `spring-ai-starter-model-openai` | `openAiChatModel` (+ 임베딩 빈) | `external-chat=true` 일 때 답변 (Upstage Solar) |
| `spring-ai-starter-model-bedrock-converse` | (자동구성) | **현재 코드에서 아무도 안 쓴다.** AWS SDK 를 끌고 오는 부작용만 남아 있다 |

> ⚠️ OpenAI 스타터는 **기동 시 `spring.ai.openai.api-key` 를 검사하고 임베딩 빈도 만든다.**
> 그래서 모든 환경에 `spring.ai.model.embedding=ollama` 가 필요하다(`build.gradle` 주석이 못박고 있다).
> 이 키를 지우면 임베딩이 OpenAI 로 붙어 벡터 공간이 바뀐다.

> ⚠️ Bedrock 스타터는 지울 수 없다고 단정하지 말 것. 다만 지우면
> `Application` 의 자동구성 exclude 와 `OpenSearchVectorStoreConfig` 의 존재 이유가 사라지므로,
> **셋을 함께 판단**해야 한다. 지금 상태에서 스타터만 빼면 OpenSearch 구성이 중복 등록될 수 있다.

---

## 2. `LlmModelConfig` — 답변 모델 결정

```java
@Configuration
@RefreshScope                    // Config Server 갱신 시 재생성된다
public class LlmModelConfig {

    @Value("${spring.ai.answer.external-chat:false}")
    private boolean externalChatEnabled;

    @Bean("answerChatModel")
    @Primary
    public ChatModel answerChatModel(ollamaChatModel, openAiChatModel, anthropicChatModel) {
        if (externalChatEnabled) return openAiChatModel;              // 외부 고정
        return new FallbackChatModel(ollamaChatModel, anthropicChatModel);
    }
}
```

- `@Primary` 라서 **`ChatModel` 을 `@Qualifier` 없이 주입하면 이게 들어온다.**
  현재 그렇게 주입하는 곳: `KeywordServiceImpl` · `EvaluationServiceImpl` · `PdfVectorService` ·
  `ToolCallingServiceImpl`. 의도한 동작이지만, 새 코드는 `ChatModelRouter` 를 쓰는 쪽이 읽기 쉽다.
- `@RefreshScope` 이므로 `POST /actuator/refresh` 로 `external-chat` 전환이 무중단으로 먹는다.
- 코드에 `anthropicChatModel` 반환이 주석으로 남아 있다. 되살릴 때는
  **답변 경로가 외부로 나간다**는 뜻이므로 데이터 반출 정책을 먼저 확인한다.

---

## 3. `ChatModelRouter` — 배정 정책

```java
chatModel()    // = answerChatModel  : 고객 데이터를 보는 모든 호출
routingModel() // = anthropicChatModel : 질문 원문만 넘기는 도구 선택 전용
```

**가르는 기준은 모델이 고객 데이터를 보느냐다.** 배정을 설정 키로 빼지 않는다 — 값 하나를
잘못 넣으면 고객 데이터가 외부로 나간다. 모델명·엔드포인트·키만 Config Server 가 정한다.

### `routingModel()` 을 쓰는 곳은 현재 둘뿐이다

| 클래스 | 넘기는 것 | 타임아웃 |
|--------|----------|----------|
| `SupportRouter` | 질문 원문 + 화면 카탈로그(도구 정의) | 20초 |
| `MultiAgentOrchestrator` | 질문 원문 + 첨부 **파일명·건수만** | 20초 |

여기에 지표·문서·요구사항 원문을 넘기는 코드를 추가하면 정책 위반이다.
`MultiAgentServiceImpl` 이 `routingText`(첨부 사실만) 와 `agentText`(첨부 행 원문)를
따로 만드는 이유가 정확히 이것이다.

---

## 4. `FallbackChatModel` — 폴백 규칙

```java
call(prompt)    → primary 실패 시 fallback.call(forFallback(prompt))
stream(prompt)  → 첫 청크가 나가기 전(emitted=false)에만 폴백. 나간 뒤면 그대로 에러 전파
```

- **스트리밍 도중 전환하지 않는다.** 이미 보낸 토큰 뒤에 다른 모델의 답이 이어지면 출력이 깨진다.
- `forFallback` 은 `new Prompt(prompt.getInstructions())` — **옵션(모델명·temperature 등)을 버린다.**
  Ollama 전용 옵션을 Anthropic 에 그대로 넘기면 400 이 난다.
- 폴백이 일어나면 `WARN` 한 줄이 남는다(`primary=` · `fallback=` · `cause=`).
  운영에서 Ollama 장애를 감지하는 신호다.
- `getDefaultOptions()` 는 **primary 것을 돌려준다.** 폴백 중에도 옵션은 primary 기준이다.

---

## 5. `OllamaWarmupRunner` — cold start

```
@PostConstruct → 데몬 스레드 "ollama-warmup" 시작
  ├─ external-chat=true   → chat 예열 생략, chatWarmedUp=true 로 표시
  └─ 아니면                → ollamaChatModel 을 직접 호출("ping")
                             실패하면 chatWarmupFailed=true (답변은 Anthropic 폴백으로 나감)
  그리고 항상 → embeddingModel.embed("ping")
```

- **예열은 `ollamaChatModel` 을 직접 부른다.** 라우터를 거치면 폴백된 Anthropic 이 대신 답해
  Ollama 가 죽었는데도 `chat=true` 로 찍힌다.
- 상태는 `static volatile` 필드다. `GET /chat/status` 가 읽는다.
  **한 번 true 가 되면 갱신되지 않는다** — 런타임 헬스체크가 아니라 기동 시 한 번의 판정이다.
- `isReady() = embeddingWarmedUp && (chatWarmedUp || chatWarmupFailed)`.
  `chatFallback=true` 여도 서비스는 정상이다(답변이 Anthropic 으로 나갈 뿐).

---

## 6. 임베딩은 Ollama 고정 — 협상 대상이 아니다

`OpenSearchVectorStoreConfig` 가 `@Qualifier("ollamaEmbeddingModel")` 로 명시 주입한다.

임베딩 모델을 바꾸면:
- 벡터 **차원과 공간이 달라진다** → 기존 인덱스를 못 쓴다
- 기존 문서와 새 문서의 유사도가 의미를 잃는다 → 검색 품질이 조용히 무너진다

바꿔야 한다면 **provider 별 별도 인덱스 + 전체 재적재**가 필요한 별도 과제다.
"임베딩만 잠깐 바꿔보자"는 없다. 요청이 오면 이 비용을 먼저 알린다.

---

## 7. 프롬프트 외부화

### 7.1 Config Server 가 주입하는 키

| 키 | 쓰는 곳 |
|----|---------|
| `prompt.support.role` | `SupportServiceImpl` — 화면 브리핑 역할 |
| `prompt.support.planner` | `SupportRouter` — 자유 입력 라우팅 시스템 메시지 |
| `prompt.support.synthesis` | `SupportServiceImpl` — 여러 화면 지표 종합 |
| `prompt.support.common` · `lens-project` · `lens-settings` | `SupportServiceImpl` — 공통/렌즈별 지침 |
| `prompt.support.targets[]` | `SupportRoutingProperties` — 화면 카탈로그(id·title·description·knowledgeArea) |
| `prompt.chat-stream.system-message` | `ChatServiceImpl` — 일반 챗 |
| `prompt.project-analysis.system-message` | `ChatServiceImpl` — 프로젝트 분석 |
| `prompt.kpi-report.system-message` | `ReportServiceImpl` |
| `prompt.performance-generate.system-message` · `performance-news.system-message` | `PerformanceServiceImpl` |
| `chat.keyword-html.*` | `KeywordHtmlMappingProperties` — LLM 우회 게이트 |
| `spring.ai.vectorstore.opensearch.{uris,index-name,similarity-function,initialize-schema}` | `OpenSearchVectorStoreConfig` |
| `spring.ai.answer.external-chat` | `LlmModelConfig` · `OllamaWarmupRunner` |
| `arms.backend.url` · `arms.engine.url` | Feign |
| `filesystem.base-directory` (기본 `/mnt/vector_file`) | `FileSystemServiceImpl` · `JsonVectorServiceImpl` |
| `report.kpi.output-path` (기본 `/data/arms/reports`) | `ReportServiceImpl` |

**기본값을 주지 않는 키**(`prompt.*` 대부분, `spring.ai.vectorstore.opensearch.uris`·`index-name`)는
Config Server 가 안 붙으면 기동이 실패한다. 이는 **의도된 fail-fast** 다 — 빈 프롬프트로 도는 것보다 낫다.
새 시스템 메시지도 기본값 없이 넣는다.

### 7.2 코드에 남겨 두는 프롬프트

에이전트 페르소나(`MultiAgentOrchestrator.SYSTEM_PROMPT` · `PmExpertAgent.SYSTEM_PROMPT`)와
스킬 지시서(`ReqToTaskSkill.INSTRUCTIONS`)는 **코드 상수**다.
도구 이름·출력 형식·판정 기호가 코드의 다른 부분과 맞물려 있어, 설정으로 빼면 따로 놀다 깨진다.
이 셋을 고칠 때는 함께 바뀌어야 할 것을 먼저 확인한다:

- 도구 이름을 바꾸면 → `MultiAgentSubAgentTools.PM_EXPERT` · `ReqToTaskSkill.NAME` ·
  `PmbokSearchTool.NAME` 상수와 오케스트레이터 `parse()` 의 비교문
- 출력 형식(판정 기호 `✅ ⚠️ ❓ 🔀 🚫 📌`)을 바꾸면 → 프론트 렌더링과 `ReqSheetWriter` 내보내기
- `답변을 "{" 로 시작하지 않는다` 규칙을 빼면 → 프론트가 본문을 진행상태 JSON 으로 오인
