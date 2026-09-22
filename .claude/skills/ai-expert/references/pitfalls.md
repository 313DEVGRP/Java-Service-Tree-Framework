# 함정 모음

착수 전에 훑고, 이상 동작이 보이면 여기부터 본다. 형식: **증상 → 원인 → 처리**.

---

## 기동이 안 된다

**`SSLException: Unsupported or unrecognized SSL message` 로 기동 실패**
→ `Application` 의 `OpenSearchVectorStoreAutoConfiguration` exclude 가 빠졌다.
AWS SDK(bedrock-converse 스타터)가 클래스패스에 있으면 자동구성이 HTTPS 강제 트랜스포트를 고른다.
→ exclude 를 되살린다. `OpenSearchVectorStoreConfig` 와 **짝**이므로 둘을 함께 본다.

**`Could not resolve placeholder 'prompt....'` 로 기동 실패**
→ Config Server 에 키가 없다. `prompt.*` 는 일부러 기본값을 안 준다.
→ Global-Config 에 키를 넣는다. **코드에 기본값을 박아서 막지 않는다** — 빈 프롬프트로 도는 것이 더 나쁘다.

**`NoUniqueBeanDefinitionException: ChatModel`**
→ 모델 스타터를 추가했는데 `@Primary` 가 정리되지 않았다.
→ `LlmModelConfig.answerChatModel` 이 유일한 `@Primary` 다. 새 모델은 `@Qualifier` 로만 쓴다.

**임베딩이 엉뚱한 모델로 붙는다**
→ OpenAI 스타터가 임베딩 빈도 만든다. `spring.ai.model.embedding=ollama` 가 빠졌다.
→ 모든 프로파일에 이 키가 있어야 한다. `build.gradle` 주석이 이 사실을 못박고 있다.

---

## 답변이 이상하다

**"AI 가 멈춘 것처럼 보인다" / LLM 을 안 부른다**
→ `chat.keyword-html.mappings` 의 키워드가 질의에 포함되어 **의도적으로 우회**된 것이다.
로그에 `[KeywordHtml] hit — keyword=... label=...` 이 남는다.
→ 코드 버그가 아니다. `chat.keyword-html.enabled: false` 또는 매핑 조정.

**검색 결과가 없을 때 "답변할 수 없습니다"만 나온다**
→ `ContextualQueryAugmenter.allowEmptyContext(false)`.
→ `RagServiceImpl.buildRagAdvisor` 는 `true` 로 둔다. 바꿀 거면 의도를 명시한다.

**답변 톤이 갑자기 달라졌다**
→ Ollama 가 실패해 Anthropic 폴백으로 넘어간 것. `FallbackChatModel :: 주 모델 실패` WARN 이 남는다.
→ 서비스는 정상이다. Ollama 쪽을 본다. `GET /chat/status` 의 `chatFallback` 도 확인.

**스트리밍 중간에 다른 모델 답이 섞인다**
→ 일어나면 안 된다. `FallbackChatModel.stream` 은 첫 청크가 나간 뒤에는 전환하지 않는다.
→ `emitted` 플래그 로직을 건드렸는지 확인한다.

**폴백 시 400 이 난다**
→ `forFallback` 이 옵션을 버리는 부분을 지웠다. Ollama 옵션을 Anthropic 에 그대로 넘기면 거부된다.
→ `new Prompt(prompt.getInstructions())` 를 유지한다.

**프론트가 답변 첫 줄을 진행상태로 오인한다**
→ 본문이 `{` 로 시작했다. 진행상태·evidence 청크가 JSON 이라 구분이 모양으로만 된다.
→ 에이전트 프롬프트의 `답변을 "{" 로 시작하지 않는다` 규칙을 유지한다.

---

## 첫 응답이 너무 느리다

**기동 직후 첫 질의가 수십 초**
→ Ollama cold start. 모델 적재 대기다.
→ `OllamaWarmupRunner` 가 예열 중이다. `GET /chat/status` 의 `ready=true` 이후에 안정된다.
**예열 로직을 지우지 않는다.**

**`chat=true` 인데 실제로는 Ollama 가 죽어 있다**
→ 예열이 라우터를 거치면 폴백된 Anthropic 이 대신 답해 true 로 찍힌다.
→ 현재 코드는 `ollamaChatModel` 을 **직접** 부른다. 라우터 경유로 바꾸지 않는다.

**파이프라인 자체가 느리다**
→ `PromptContextServiceImpl :: build 완료 [느린 요청 감지 {}ms]` 를 본다.
RAG(1) → Keyword(LLM 2회!) → SearchEngine(1) 이 직렬이다. Keyword 2회 호출이 대개 범인이다.
→ `keywordCount <= 1` 이면 2단계를 건너뛴다. 줄일 수 있는지 검토한다.

---

## 도구·에이전트가 안 돈다

**모델이 도구를 고르는데 아무것도 수집되지 않는다**
→ 도구 이름 / pageKey / collector `PAGE_KEY` 3자가 어긋났다.
`SupportRouter :: 알 수 없는 도구` 또는 `SupportToolsService :: collector 없음` WARN 이 남는다.
→ **둘 다 예외 없이 조용히 실패한다.** 세 이름을 맞춘다.

**진행 문구에 pageKey 원문(`reqGantt` 같은)이 그대로 보인다**
→ Config Server `prompt.support.targets[]` 에 그 id 의 `title` 이 없다.
→ 카탈로그에 추가한다. 화면 추가는 **collector · @Tool · targets 셋 다**가 한 세트다.

**도구가 전혀 호출되지 않는다**
→ `supportToolsService.toolCallbacks()` 가 비었다(`도구 카탈로그가 비어 있음` WARN).
`@PostConstruct registerCallbacks()` 가 도는지, `@Tool` 메서드가 public 인지 확인한다.

**서브에이전트 호출이 20초에 끊긴다**
→ `ORCHESTRATION_TIMEOUT` / `ROUTING_TIMEOUT` 이 20초다. 외부 모델 지연이다.
→ 타임아웃을 늘리기 전에 라우팅 프롬프트가 너무 긴지 본다. 라우팅엔 질문 원문만 가야 한다.

**도구 실행 중 예외가 나서 대화가 통째로 깨진다**
→ 도구가 예외를 던졌다.
→ 도구는 예외 대신 **값**(`"검색 실패"` · `"검색 결과 없음"` · 빈 `Map`)을 돌려준다.

**PM expert 가 변환 규칙을 안 따른다**
→ `req_to_task` 스킬을 호출하지 않았다. 규칙이 통째로 빠진다.
→ `PmExpertAgent` 는 `.tools(...)` 로 **내부 실행을 켠 채** 붙여야 한다.
오케스트레이터처럼 `internalToolExecutionEnabled(false)` 를 주면 안 된다.

---

## 데이터가 0 으로 나온다

**지표가 전부 0 / 목록이 비었다**
→ Feign 응답 VO 필드가 상대 모듈과 어긋나 역직렬화가 조용히 비었다. **에러가 안 난다.**
→ `BackendCore*VO` · `SearchEngineDocumentVO` 를 상대 모듈 응답과 1:1로 맞춘다.
한쪽을 바꾸면 양쪽을 바꾸고 `docs/ai/11_changelog` 에 남긴다.

**필터를 걸었더니 0건이다**
→ 메타데이터 키를 새로 추가했는데 기존 색인 문서에는 그 키가 없다.
→ 필터에 쓸 키는 **전체 재적재와 세트**다.

**같은 문서가 중복 검색된다**
→ `deleteByPath(path)` 없이 `save(documents)` 만 했다.
→ 재적재는 항상 선삭제 → 저장 순서.

---

## 리액티브

**부하가 걸리면 전체가 멎는다**
→ 이벤트 루프에서 블로킹 호출(VectorStore · `ChatClient...call()` · Feign · POI · 파일 IO).
→ `Mono.fromCallable(...).subscribeOn(Schedulers.boundedElastic())` 로 격리한다.

**`streamStatus` 맵이 계속 커진다 (메모리 누수)**
→ `doOnComplete`/`doOnError` 만 쓰면 **클라이언트가 끊었을 때(cancel)** 제거가 안 된다.
`RagServiceImpl` · `AiRequestServiceImpl` · `ChatServiceImpl` 이 이 옛 방식이다.
→ 새 코드는 `Flux.defer(...).doFinally(sig -> streamStatus.remove(id))` 를 쓴다.

**`stopStream` 이 안 먹는다**
→ 플래그만 세우고 `takeUntil` 이 **다음 청크가 올 때** 판정한다. 모델이 멈춰 있으면 즉시 끊기지 않는다.
→ 의도된 동작이다. 즉시 끊으려면 구독 자체를 취소하는 별도 설계가 필요하다.

**큰 파일 업로드가 깨진다**
→ `@RequestBody` DTO 로 받으면 WebFlux 코덱 집계 한도(기본 256KB)에 걸린다.
→ `Flux<DataBuffer>` 로 받아 `DataBufferUtils.join(body, MAX)` 에서 상한을 건다(`ReqSheetService` 패턴).

---

## 문서·주석을 믿지 말아야 하는 곳

코드가 정본이다. 아래는 **현재 코드와 다른 것이 확인된** 서술이다.

| 위치 | 적힌 것 | 실제 |
|------|--------|------|
| 루트 `README.md` | Boot 3.4.4 · `SampleController` · `SafeGuardAdvisor` · `MyPagePdfDocumentReader` | Boot 3.5.6 · 해당 클래스들 없음 |
| `ReportServiceImpl` 클래스 주석 | "provider 값으로 Ollama ↔ Bedrock 분기" | `chatModelRouter.chatModel()` 하나만 사용 |
| `SupportToolsService` 주석 | "20개 노출, detail_dashboard 제외" | `@Tool` 21개 전부 노출(담당자 해석 로직이 나중에 붙었다) |
| `SupportRouter` 클래스 주석 | "이 클래스가 라우팅 모델을 쓰는 유일한 곳" | `MultiAgentOrchestrator` 도 쓴다 |
| `RagServiceImpl.DEFAULT_TOP_K` / `DEFAULT_THRESHOLD` | 기본값처럼 보임 | **어디서도 참조하지 않는 죽은 상수.** 실제 값은 호출부가 넘긴다 |
| `docs/ai/06_domain_playbooks/llm-provider.md`, `12_known_issues` | Bedrock 을 답변 대안으로 서술 | 현재 폴백은 Anthropic, 외부 전환 시 OpenAI |
| `docs/ai/**/engine-fire-*.md`, `06_page_playbooks/` | — | 폐기 대상 |

---

## 손대기 전에 비용을 먼저 알려야 하는 요청

| 요청 | 숨은 비용 |
|------|----------|
| "임베딩 모델 바꿔줘" | 벡터 공간이 바뀜 → **인덱스 전량 재적재**. 부분 전환 불가 |
| "메타데이터에 필드 하나만 추가" | 기존 문서엔 없음 → 필터로 쓰려면 **재적재** |
| "청킹 방식 개선" | **재적재** |
| "프롬프트 문구 수정" | 이 저장소가 아니라 **Global-Config(Gitea)** 변경 |
| "라우트/권한 추가" | 이 저장소가 아니라 **Middle-Proxy + Global-Config** |
| "Feign 응답에 필드 추가" | **상대 모듈(Backend-Core · Engine-Fire) 동반 변경** |
| "Support 화면 추가" | collector + `@Tool` + `prompt.support.targets[]` **3곳** |
| "테스트 붙여줘" | `src/test` 가 **아예 없다**. 테스트 소스셋부터 만들어야 한다 |
| "`/anonymous/**` 경로 추가" | MABC 대회용 임시 우회다. 인증 정책 확인 없이 따라 만들지 않는다 |

---

## 확인하지 않은 채 단정하지 말 것

- **`api/util/advisors` 3종**(`SimpleLogAdvisor` · `MessageGuardAdvisor` · `ReReadingAdvisor`)은
  `AdvisedRequest`/`AdvisedResponse` 기반 `BaseAdvisor` 를 구현한다. 이 API 는 Spring AI 마일스톤 사이에
  바뀐 이력이 있다. 손대기 전에 **현재 BOM(M8)의 `BaseAdvisor` 시그니처를 직접 확인**하고,
  `./gradlew compileJava` 로 검증한다. 기억으로 고치지 않는다.
- `MessageGuardAdvisor` 는 허용 메시지가 `"주간 보고"` · `"KPI"` **완전 일치 2개뿐**이고
  아니면 예외를 던진다. 새 경로에 붙이기 전에 허용 목록을 본다.
- `TtsClient` 는 더미다. `ExternalServiceStatus` 의 TTS 플래그는 **한 번 꺼지면 다시 안 켜진다.**
