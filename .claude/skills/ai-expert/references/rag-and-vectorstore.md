# RAG · OpenSearch VectorStore

---

## 1. VectorStore 는 수동 구성이다 (건드리지 말 것)

### 왜

```
bedrock-converse 스타터 → AWS SDK 가 클래스패스에 상주
   → M8 OpenSearchVectorStoreAutoConfiguration 이 AwsOpenSearchConfiguration 분기를 선택
      → AwsSdk2Transport 생성 (HTTPS 강제)
         → 평문 HTTP 로 노출된 자체 호스팅 OpenSearch 접속 시
            SSLException: Unsupported or unrecognized SSL message → 기동 실패
```

### 어떻게 풀었나

```java
// Application.java
@SpringBootApplication(exclude = { OpenSearchVectorStoreAutoConfiguration.class })

// OpenSearchVectorStoreConfig.java
@Bean OpenSearchClient openSearchClient()      // ApacheHttpClient5 트랜스포트 (http 스킴 그대로)
@Bean OpenSearchVectorStore vectorStore(client, @Qualifier("ollamaEmbeddingModel") EmbeddingModel)
```

**이 두 곳은 짝이다.** exclude 를 지우면 자동구성이 되살아나 기동이 깨지고,
`OpenSearchVectorStoreConfig` 를 지우면 `VectorStore` 빈 자체가 없어진다.

설정 키: `spring.ai.vectorstore.opensearch.{uris, index-name, similarity-function(기본 cosinesimil), initialize-schema(기본 true)}`.
`uris` 와 `index-name` 은 **기본값이 없다** — Config Server 가 반드시 줘야 한다.

---

## 2. 검색 파라미터 표 (코드에 박힌 값)

| 호출부 | topK | threshold | filterExpression | 목적 |
|--------|------|-----------|------------------|------|
| `RagServiceImpl` 클래스 상수 | 5 | 0.7 | — | 기본값(현재 직접 쓰는 호출부는 없다) |
| `UserQueryServiceImpl` | 2 | 0.7 | — | 프레임워크 기본 RAG |
| `PromptContextServiceImpl` | 2 | 0.7 | — | 파이프라인 [1]단계 |
| `ChatServiceImpl` | 2 | 0.7 | — | PMBOK 참고 문서 |
| `SupportServiceImpl` | 1 | 0.5 | `chunk_type == 'content'` | 브리핑 근거 1건 |
| `PmbokSearchTool` | 3 | 0.5 | `chunk_type == 'content'` | 에이전트 근거 검색 |
| `EvaluationServiceImpl` | 3 | 0.7 | — | 평가용 컨텍스트 자동 수집 |

- **threshold 0.5 vs 0.7 의 의미**: 근거 검색(0.5)은 "멀어도 일단 가져와 근거로 보여준다",
  컨텍스트 증강(0.7)은 "확실한 것만 프롬프트에 넣는다". 바꿀 때 어느 쪽인지 먼저 정한다.
- `SupportServiceImpl` 은 `knowledgeArea` 가 있을 때만 검색하고, 검색어를
  `"분류: " + knowledgeArea + "\n" + queryText` 로 만든다(메타데이터 태그가 본문에 심어져 있어 매칭이 붙는다).
- 검색 실패는 **증강 없이 진행**한다(`onErrorResume` → `Mono.empty()`). 답변 자체를 막지 않는다.

---

## 3. 문서 메타데이터 스키마

`MarkdownChunkMetadataVO.toMap()` 이 정본이다. OpenSearch 필드명은 snake_case.

| 키 | 타입 | 예 |
|----|------|-----|
| `source` | string | `PMBOK 4th Edition` |
| `file_name` | string | `page_050.md` |
| `page_number` | string | `18`, `XXIII` |
| `chapter` | int (없으면 0) | `2` |
| `chapter_title` | string | `프로젝트 생애 주기 및 조직` |
| `section` | string | `2.1.2` |
| `section_title` | string | `제품과 프로젝트 생애 주기 관계` |
| `process_group` | string[] | `["실행","계획"]` |
| `knowledge_area` | string[] | `["통합 관리","범위 관리"]` |
| `keywords` | string[] | `["프로젝트 헌장","WBS"]` |
| **`chunk_type`** | string | `content` \| `summary` |
| **`hierarchy_path`** | string | `챕터제목 > 절제목` |
| `has_diagram` | boolean | |
| `diagram_title` | string | |

`toMap()` 은 `Map.ofEntries` 라서 **null 을 못 넣는다.** 새 키를 추가할 때 `nullSafe(...)` 로 감싼다.

### 필터에 쓰는 키를 늘릴 때

기존 색인 문서에는 그 키가 **없다**. 필터가 조용히 0건을 돌려준다.
→ 키 추가는 **전체 재적재와 세트**다. 재적재 없이 추가하려면 "없을 수도 있다"를 전제로 쿼리를 짠다.

`PmbokSearchTool.label()` 은 출처 표기에 `source · (section_title | hierarchy_path) · p.page_number` 를 쓴다.
`SupportServiceImpl` 의 참고 문서 표기와 같은 규칙이다. 한쪽만 바꾸면 화면마다 출처 모양이 달라진다.

---

## 4. 적재 경로

### 4.1 Markdown (`POST /ai/markdown/vectorize`)

```
MarkdownDocumentParserService.parseContent(content, fileName)
  ① YAML Front Matter(--- ... ---) → MarkdownChunkMetadataVO
  ② 본문에서 "## 벡터 DB 검색용 전문" 섹션 → summary 청크
  ③ 그 섹션을 뺀 나머지 → content 청크
  ④ 각 청크 텍스트를 보강:  [hierarchy_path]\n\n 분류: 태그\n\n 본문 \n\n키워드: ...
```

**파일당 최대 2청크.** 빈 페이지는 건너뛴다. 텍스트 보강(`buildEnrichedText`)이
계층·분류·키워드를 본문에 심기 때문에 `"분류: ..."` 로 시작하는 검색어가 잘 맞는다 —
`SupportServiceImpl.buildSearchQuery` 가 이걸 노린다.

### 4.2 PDF (`POST /pdf/vectorize`, `GET /pdf/document-reader`)

```
ParagraphPdfDocumentReader(목차 기반 텍스트)
  + PDFBox 렌더링 → 멀티모달 모델로 이미지 설명 추출
  → TokenTextSplitter.split(...)
  → vectorStore.add(...)
```

기본 경로가 `classpath:markdown/PMBOK_4th_Edition.pdf` 로 박혀 있다.
`getDocsFromPdf` 는 `ByteArrayResource` 를 익명 하위 클래스로 감싸 `getFilename()` 을 되살린다 —
PDF 리더가 파일명을 요구하기 때문이다. 지우면 NPE 가 난다.

### 4.3 JSON / NDJSON (`/admin/vector`, `/admin/vector/ndjson`)

두 가지 모드가 있다.

**(가) 수동 분류 후 적재**
```
GET  /admin/vector/classify?path=...     → 필드 역할 자동 제안(FieldClassificationResponseVO)
POST /admin/vector  [VectorizedDTO...]   → 확인된 역할로 적재
```
역할은 `FieldRole` 3종: `CONTENT`(본문) · `CONTENT_COMPONENT`(본문 구성요소) · `METADATA`(필터용).

적재는 `deleteByPath(path)` → `save(documents)` 순서다. **선삭제를 빼면 중복이 쌓인다.**

**(나) 자동 분류 + 2-pass 스트리밍** (`POST /admin/vector/auto-classify?dirPath=...`)
```
1pass: JsonSectionAnalyzer.analyze()  → 섹션별 구조 파악(샘플링)
2pass: JsonStreamContext 로 다시 흘리며 DocumentBatchWriter 로 배치 저장
```
대용량 JSON 을 메모리에 올리지 않으려는 구조다. 파일 하나가 실패해도 건너뛰고 계속한다.

`filesystem.base-directory`(기본 `/mnt/vector_file`) 하위 경로만 읽는다.
`FileSystemServiceImpl.resolvePath` 가 정규화 후 base 밖이면 **base 로 되돌린다**(예외를 던지지 않는다).

### 4.4 재적재 판단 기준

| 바꾼 것 | 재적재 필요? |
|---------|-------------|
| 검색 topK/threshold | 아니오 |
| 필터 표현식 | 아니오 (단, 해당 키가 기존 문서에 있는지 확인) |
| 메타데이터 키 추가/이름 변경 | **예** |
| 청킹 전략(`buildEnrichedText` · summary 추출 패턴) | **예** |
| 임베딩 모델 | **예 — 인덱스 전량** |
| `similarity-function` | **예** (인덱스 매핑이 바뀐다) |

---

## 5. 평가 (`/evaluation`)

Spring AI 내장 평가기를 그대로 쓴다.

| 엔드포인트 | 평가기 |
|-----------|--------|
| `POST /evaluation/relevancy` | `RelevancyEvaluator` — 답이 질문·문맥과 관련 있는가 |
| `POST /evaluation/fact-checking` | `FactCheckingEvaluator` — 답이 문서로 뒷받침되는가 |
| `POST /evaluation/all` | 둘 다 |
| `POST /evaluation/all-with-context` | VectorStore 에서 컨텍스트를 자동 수집(topK 3, threshold 0.7)한 뒤 둘 다 |

점수는 `pass` 를 1.0/0.0 으로 환산한 것뿐이다. **연속 점수가 아니다** — 리포트에 쓸 때 주의한다.
평가기는 `@Primary` `ChatModel`(= 답변 모델)로 스스로를 채점한다. 엄밀한 벤치마크가 필요하면
별도 심판 모델을 두는 것이 맞고, 그건 현재 구조에 없다.
