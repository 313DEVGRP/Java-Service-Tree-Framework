# 도메인별 규칙

각 도메인을 건드리기 전에 해당 절만 읽으면 된다.

---

## chat — `/chat` (`ChatServiceImpl`)

`UserQueryAbstractController` 상속. 입력은 `ChatDTO`
(`pdServiceId` · `pdServiceVersionIds` · `attachedWikiDocs` · `attachedRagDocs`).

```
stream(query)
  ├─ pdServiceId == null  → chatStream()          : RAG 컨텍스트 + prompt.chat-stream.system-message
  └─ pdServiceId != null  → projectAnalysisStream(): Engine-Fire 집계를 붙인 프로젝트 분석
```

프로젝트 분석 스트림은 **3개 청크를 순서대로** 보낸다.
1. `formatProjectInfo(...)` — 마크다운 제품·버전 헤더
2. `toJson(analysis)` — 집계 원자료 JSON + `\n\n`
3. LLM 답변 스트림 (`prompt.project-analysis.system-message`)

**이 순서와 모양이 프론트 계약이다.**

### RAG 컨텍스트 결정 규칙

```java
attachedRagDocs 가 비어있지 않으면 → 그걸 쓰고 VectorStore 검색을 생략
아니면 → searchPmbok(topK 2, threshold 0.7)
```
클라이언트가 이미 문서를 골라 보냈으면 다시 검색하지 않는다. 검색 비용과 일관성 둘 다를 위한 것이다.

### 사용자 프롬프트 조립 순서 (고정)

`[사용자 질의]` → (분석일 때) `[프로젝트 집계 데이터]` → `[PMBOK 참고 문서]` → `[Wiki 참고 문서]`

- `generate` 와 `buildContext` 는 프레임워크 `UserQueryServiceImpl` 에 위임한다.
  **`stream` 과 `generate` 의 동작이 다르다** — `generate` 는 프로젝트 분석을 하지 않는다. 의도된 차이인지 확인하고 손댄다.
- 우선순위/난이도 한글 라벨 표(`PRIORITY_LABELS` · `DIFFICULTY_LABELS`)는 Engine-Fire 키와 1:1이다. 키가 바뀌면 여기도 바뀐다.
- `POST /chat/context` 로 파이프라인 컨텍스트만 따로 볼 수 있다(디버깅용).

---

## support — `/support` (`SupportServiceImpl`)

가장 복잡한 도메인. 흐름 전체는 `references/agents-and-tools.md` §1 에 있다. 여기서는 나머지만 적는다.

### 두 갈래 입력

| 조건 | 경로 |
|------|------|
| `pageKey` 있음 | 화면 브리핑 — collector 1개 + (knowledgeArea 있으면) PMBOK 근거 1건 |
| `pageKey` 없음 | 자유 입력 — `SupportRouter` 로 화면을 고름 (최대 2개) |

### 시스템 메시지 선택

`resolveSystemMessage(query)` 가 `prompt.support.{role, common, lens-project, lens-settings}` 를 조합한다.
자유 입력 종합은 `prompt.support.synthesis` 를 쓴다. **렌즈(project/settings) 구분은 화면 성격**이다.

### 담당자 해석 (`SupportAssigneeResolver`)

`detail_dashboard` 는 "누구의" 지표인지가 필요하다. `assigneeEmail` 이 없으면 질의문에서 이름을 뽑아
Backend-Core 사용자 그룹에서 찾는다. 결과는 4가지다.

| `Resolution` | 의미 | 처리 |
|-------------|------|------|
| `matched` | 1명 확정 | 그대로 진행 |
| `ambiguous` | 동명이인 | `{"assigneePick":{ambiguous:true,...}}` 로 되물음 |
| `missingEmail` | 이름은 찾았으나 이메일 없음 | `{"assigneePick":{missingEmailName:"..."}}` |
| `notFound` | 못 찾음 | 후보 목록과 함께 되물음 |

되물을 때는 **스트림을 거기서 끝낸다.** 추측해서 아무 담당자나 고르지 않는다.

이름 추출은 `SupportAssigneeNames` 가 **Lucene Nori 한국어 형태소 분석기**(`lucene-analysis-nori`)로
질의문에서 인명 후보를 뽑는다. 한글 자모 분해 표와 로마자 성씨 표까지 들고 있어
`"홍길동"` · `"Hong Gildong"` 을 함께 맞춘다(이름 길이 2~4자).
**이 저장소에서 Nori 를 쓰는 유일한 곳이다** — `build.gradle` 의 lucene 의존성이 여기 때문에 있다.

### 지표 수집 실패 규칙

collector 는 예외를 밖으로 던지지 않는다. 원천 조회가 실패하면 `PageMetricSupport.anyFailed(...)` 로 판단해
**빈 VO** 를 돌려준다 → evidence 에서 빠지고 → 진행 문구가 `지표가 없어요` 가 된다.
화면 하나가 죽어도 나머지 브리핑은 나간다. **이 관용을 없애면 Backend-Core 장애가 곧 Support 전면 장애가 된다.**

---

## multiagent — `/anonymous/multiagent` (`MultiAgentServiceImpl`)

상세는 `references/agents-and-tools.md` §2.

- `sessionId` 가 비면 `IllegalArgumentException` 으로 즉시 에러. (다른 도메인보다 엄격하다)
- 오케스트레이터가 툴콜도 텍스트도 안 주면 `FALLBACK_ANSWER`(요구사항을 붙여넣어 달라는 안내)를 낸다.
- 진행 문구는 2개: `질문을 이해하고 있어요` → `PM expert agent 에게 맡겼어요`.
- 첫 토큰 도착 시각을 `INFO` 로 남긴다. 체감 지연 조사 시 이 로그를 본다.
- 스트림 정리는 `doFinally` 로 한다 (**이 도메인이 올바른 패턴이다**).
- 엑셀 파싱/내보내기는 `ReqSheetService` — 서버는 파일을 **저장하지 않는다**. 상한 5MB.

---

## report — `/report/kpi/generate` (`ReportServiceImpl`)

```
[1/4] Engine-Fire KPI 5종 수집 (project-status · requirement-overview · time-compliance · contribution · quality)
[2/4] LLM 분석문 생성 (prompt.kpi-report.system-message 에 KPI 요약 주입)
[3/4] Apache POI XMLSlideShow 로 PPT 작성 (960x540, 제목색 #1F3864)
[4/4] 완료 — filePath · fileSizeBytes 반환
```

- 진행 상황은 `DwrClient.sendMessage(...)` 로 밀어 보낸다(`PerformanceServiceImpl` 관행).
- 오래 걸려서 `heartbeatScheduler`(단일 스레드)로 하트비트를 보낸다. `@PreDestroy` 에서 `shutdownNow()` —
  **스케줄러를 추가하면 종료 처리도 같이 넣는다.**
- 출력 경로는 `report.kpi.output-path`(기본 `/data/arms/reports`). 서버 로컬 디스크에 쓴다.
- 전체가 블로킹이라 `Mono.fromCallable(...).subscribeOn(boundedElastic())` 하나로 감싼다.
- ⚠️ **클래스 주석이 오래됐다** — "provider 값으로 Ollama ↔ Bedrock 분기" 라고 적혀 있으나
  현재 코드는 `chatModelRouter.chatModel()` 하나만 쓴다. 주석을 믿지 말 것.

---

## performance — `/performance` (`PerformanceServiceImpl`)

| 엔드포인트 | 하는 일 |
|-----------|---------|
| `POST /performance/generate` | 개인 성과 생성문 (`prompt.performance-generate.system-message`) |
| `POST /performance/analysis-script` | 성과 분석 스크립트 (`prompt.performance-news.system-message`) |
| `POST /performance/analysis` | 성과 분석 |

- 원천은 `EngineClient.getPerformanceAssigneeAggregation` (롤링 3개월 담당자 집계).
- 진행 상황을 `DwrClient` 로 푸시한다.
- ⚠️ **`MessageGuardAdvisor` 가 실제로 걸려 있다** —
  `.advisors(simpleLogAdvisor, retrievalAugmentationAdvisor, messageGuardAdvisor)`.
  **허용 메시지가 `"주간 보고"` · `"KPI"` 완전 일치 2개뿐**이고 그 외에는 `IllegalArgumentException` 을 던진다.
  즉 **이 경로는 저 두 문장으로만 호출된다.** 사용자가 "왜 성과 분석이 안 되냐"고 하면 여기부터 본다.
  허용어를 늘리려면 `MessageGuardAdvisor.ALLOWED_MESSAGES`(코드 상수)를 고쳐야 한다.

---

## evaluation — `/evaluation` (`EvaluationServiceImpl`)

상세는 `references/rag-and-vectorstore.md` §5. 점수는 pass 를 1.0/0.0 으로 바꾼 것뿐이다.

---

## 적재 (`/ai/markdown` · `/pdf` · `/admin/vector` · `/admin/vector/ndjson`)

상세는 `references/rag-and-vectorstore.md` §4.

핵심만:
- Markdown = 파일당 최대 2청크(content + summary)
- 재적재는 `deleteByPath` → `save` 순서
- JSON 자동 분류는 1pass(섹션 분석) → 2pass(스트리밍 저장)

---

## filesystem — `/admin/filesystem` (`FileSystemServiceImpl`)

벡터화 대상 파일을 서버에서 올리고/보고/지우는 관리 API.
루트는 `filesystem.base-directory`(기본 `/mnt/vector_file`).

| 엔드포인트 | |
|-----------|---|
| `GET /directories` · `GET /file` | 조회 |
| `POST /upload` (multipart) · `POST /directory` | 생성 |
| `DELETE /files` · `DELETE /directory` | 삭제 |

- `resolvePath` 가 정규화 후 base 밖이면 **예외 대신 base 로 되돌린다**(`WARN` 만 남는다).
  경로 이탈을 막지만 **호출자는 실패를 모른다** — 조용히 엉뚱한 목록이 나올 수 있다.
- 파일 삭제 API 이므로 **인증 경로 밖에 노출되면 안 된다.** 새 엔드포인트를 붙일 때
  Middle-Proxy 의 라우트/권한 반영이 필요한지 반드시 확인한다.

---

## search — `/ai/search` (`SimilaritySearchServiceImpl`)

VectorStore 유사도 검색을 그대로 노출한다. `GET` 은 질의만, `POST` 는 `topK`·`threshold`·필터를
요청 본문으로 받는다. **파라미터가 클라이언트에서 온다** — RAG 경로(코드에 상수로 박힌 값)와 다르다.

---

## tts — `/tts/convert` (`TtsServiceImpl`)

현재 `TtsClientDummyImpl` 로 **더미 처리**되어 있다(`TtsClient` 의 `url` 기본값도 가짜다).
실패하면 `ExternalServiceStatus.markTtsUnavailable()` 로 **전역 플래그를 끄고** 예외를 던진다.
이 플래그는 **한 번 꺼지면 다시 켜지지 않는다**(`GET /status` 가 읽는다).
살릴 때는 복구 경로를 함께 만든다.

---

## toolcalling — `/tool-calling/stream` (`ToolCallingServiceImpl`)

wttr.in 날씨 조회 데모. 프로덕션 경로가 아니다. `returnDirect = true` 예시가 여기 있다.

---

## sample — `/sample/query` (`SampleQueryServiceImpl`)

**aigenerate 7단계 레퍼런스 구현.** 새 도메인을 만들 때 여기를 베낀다.
상속 4개 엔드포인트 외에 `/execute` · `/execute-stream` · `/context` · `/save` · `/save-all` 이 있다.
운영 트래픽은 없지만 **파이프라인이 살아 있는지 확인하는 용도**로 남겨 둔다.

---

## 상태 조회

| 엔드포인트 | 내용 |
|-----------|------|
| `GET /chat/status` | Ollama 예열 상태 (`chat` · `embedding` · `chatFallback` · `ready` · `checkedAt`) |
| `GET /anonymous/chat/status` | 위와 동일. **MABC 대회용 임시 경로 — `TODO: 대회 이후 원복 필요`** |
| `GET /status` | 외부 서비스 가용성 (현재 TTS 하나) |
