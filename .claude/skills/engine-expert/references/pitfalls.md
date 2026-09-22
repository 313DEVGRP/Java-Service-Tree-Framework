# 함정 목록과 리뷰 체크리스트

실제 코드·커밋·저장소 문서에서 확인한 것만 적는다. 새 함정은 `docs/ai/12_known_issues/guide.md` 에도 남긴다.

---

## 1. 조용히 틀리는 것들 (에러가 안 나서 가장 위험)

### 1.1 `recent` 를 빼먹은 집계
- **증상:** 건수가 실제보다 많다. 에러는 없다.
- **원인:** `AlmIssueEntity` 는 이슈 1건당 이력 문서가 여러 개다. `aggregate*` 는 이력 전체를 센다.
- **해결:** "현재 상태"를 보는 집계는 반드시 `aggregateRecent*` / `findRecentHits` / `findAllRecentDocsBySearchAfter`.
  직접 `andTermQueryFilter("recent", true)` 로 붙이지 말고 `*Recent*` 메서드를 쓴다.

### 1.2 멀티필드에 `.keyword` 누락
- **증상:** 집계 버킷이 비거나 `진행 중` 이 `진행`/`중` 으로 쪼개져 나온다.
- **원인:** `status.status_name` 은 `text` + `.keyword` 멀티필드인데 타입을 생략.
- **해결:** 집계·필터·정확일치는 `.keyword`. **단, `armsStateCategory`·`key`·`recent_id` 등 단독 keyword 는 접미사 없음.**
  구분은 `docs/almIssueEntity.md` 매핑에서 확인.

### 1.3 `valueByName`/`countByName` 의 alias 오타
- **증상:** 빈 문자열(`""`) 또는 `0` 이 나온다. 예외 없음.
- **원인:** `DocumentBucket` 은 alias 가 안 맞으면 부모로 거슬러 올라가다 루트에서 기본값을 반환한다.
- **해결:** `mainFieldAlias`/`subFieldAlias` 로 지정한 문자열과 **정확히** 일치시킨다.

### 1.4 `RangeQueryFilter` 에 null/빈문자열
- **증상:** 기간 조건이 통째로 사라져 전체 데이터가 집계된다.
- **원인:** `RangeQueryFilter` 는 null·빈 문자열이 오면 **필터 자체를 무효화**한다(관용 설계).
- **해결:** 반드시 걸어야 하는 범위는 호출 전에 값을 검증하고, 기본값을 준비한다.

### 1.5 `SearchRequestDTO.size` 기본값 10
- **증상:** 검색 결과가 10건만 나온다.
- **원인:** `SearchRequestDTO` 기본 `size = 10` (내부 `SearchDocDTO` 는 10000이라 혼동하기 쉽다).
- **해결:** `SimpleQuery.search(...)` 경로에서는 `size` 를 명시한다.

### 1.6 terms 집계로 전량을 뽑으려 함
- **증상:** 일부 버킷이 누락되거나 OpenSearch 메모리 압박.
- **원인:** terms 는 Top N 용이라 정확한 전량 집계를 보장하지 않는다.
- **해결:** 전량 순회는 `compositeAllHits` / `compositeRecentAllHits`(`after_key` 기반).

---

## 2. 기동이 깨지는 것들 (fail-fast)

### 2.1 `EntityClassConfig` Wrapper Bean 누락
- **증상:** 새 엔티티용 `EsCommonRepositoryWrapper<X>` 주입 실패로 컨텍스트가 안 뜬다.
- **해결:** `config/EntityClassConfig` 에 `@Bean ... repositoryOf(X.class)` 추가.

### 2.2 `EsCommonRepository` 를 직접 필드로 보유
- **증상:** `EsCommonRepository 타입을 변수로 가질 수 없습니다.` 또는
  `공통저장소를 구현한 클래스는 변수로 사용 하실수 없습니다.`
- **원인:** `RepositoryConfiguration` 의 `ApplicationListener` 가 기동 시 스캔해 막는다.
- **해결:** 항상 `EsCommonRepositoryWrapper<E>` 를 주입한다.

### 2.3 `EsCommonRepository` 상속 인터페이스에 메서드 선언
- **증상:** `공통저장소를 상속한 인터페이스는 메소드를 가질수 없습니다.`
- **해결:** 메서드를 하나도 선언하지 않는다. 필요한 기능은 Wrapper 에 있다.

### 2.4 `@FeignClient(name=...)` 중복
- **증상:** 빈 이름 충돌로 기동 실패. 과거 실제 발생(커밋 `4b19395f` "FeignClient 이름 중복").
- **해결:** name 을 전역 유일하게 짓는다.

### 2.5 전략 구현체가 같은 `ServerType` 을 중복 신고
- **증상:** `*StrategyFactory` 생성자의 `Collectors.toMap` 이 `IllegalStateException`.
- **해결:** `getServerType()` 반환이 겹치지 않게 한다.

---

## 3. 문서와 코드가 어긋난 지점 (2026-09-22 확인)

| `docs/ai` 서술 | 실제 |
|----------------|------|
| Feign 은 `msa_communicate/` | **`openfeign/`** 으로 개명 (커밋 `762ca582`, 2026-08-28) |
| `issue/almapi/redisbuffer` · `IssueBufferSender` · `MiddleProxyIssueBuffer` | **존재하지 않음.** 실제 대량 처리는 `IssueSaveTemplate` 의 기간 청크 순회 |
| 디렉터리 문서의 `issue/*` 목록 | `issue/discovery`·`issue/directfetch` 누락 |

→ `docs/ai` 를 근거로 파일을 찾다 없으면 **개명/삭제를 의심하고 `git log --diff-filter=D --name-only -- "*패턴*"`** 으로 확인한다.
코드가 정본이다.

---

## 4. 설계 경계 혼동

### 4.1 Engine-Fire 에 Spring AI 를 넣으려 함
- **원인:** `/ai-search` 엔드포인트가 있어 AI 본체로 오인.
- **사실:** Spring AI·Ollama·VectorStore 는 **별도 모듈 `Java-Service-Tree-Framework-AI`**.
  이 저장소 `build.gradle` 에 Spring AI 의존성이 없다.
- **해결:** Engine-Fire 는 RAG 의 **데이터 제공자**(wiki 키워드 검색)까지만.

### 4.2 컨트롤러를 WebFlux 로 바꾸려 함
- **사실:** 이 저장소에서 WebFlux 는 **외부 ALM I/O 전용**이다. 컨트롤러는 Spring MVC.
- **해결:** `Mono`/`Flux` 를 컨트롤러 반환 타입으로 쓰지 않는다. Middle-Proxy 와 혼동 금지.

### 4.3 `AiSearchDocumentVO` ↔ `SearchEngineDocumentVO` 필드 어긋남
- **증상:** AI 서비스에서 역직렬화 실패·필드 누락.
- **해결:** 두 VO 는 1:1 유지. 한쪽 변경 시 양쪽 동시 수정 + `docs/ai/11_changelog` 기록.

### 4.4 `MAX_RESULTS` 단독 상향
- **증상:** AI RAG 응답이 잘리거나 품질 저하.
- **해결:** AI 서비스의 `num_ctx`·`num-predict` 와 함께 검토.

---

## 5. 설정·운영

### 5.1 인덱스명 하드코딩
- **해결:** `arms-index-name.*` → `ElasticsearchIndexNameConfig` Bean(`#{@jiraissue}` 등) 또는
  `wrapper.indexAliasName()`. 리터럴 금지.

### 5.2 Jira 엔드포인트·JQL 하드코딩
- **증상:** `/rest/api/2` ↔ `/rest/api/3` 혼용, JQL 이 파일마다 다름.
- **해결:** `jira.api.*`·`redmine.api.*`·`alm.discovery.*` 설정 템플릿 조합. 현재 base 는 `/rest/api/3`,
  검색은 `/search/jql`, `maxResults: 25`.

### 5.3 429 를 동기 호출로 우회
- **해결:** WebFlux + `Retryable429Exception(delaySeconds)` 재시도 경로 유지.

### 5.4 Reactive Elasticsearch 자동설정
- **증상:** Reactive ES 빈/헬스가 끼어들어 기동·헬스 오류.
- **해결:** 설정의 `spring.autoconfigure.exclude`(Reactive ES 자동설정)와
  `management.health.elasticsearch.enabled: false` 를 임의로 풀지 않는다.
  헬스는 `CustomElasticsearchHealthIndicator` 가 담당한다.

### 5.5 평문 시크릿
- **사실:** Global-Config 주입 yml 에 `aes.token`·`slack.token` 이, `build.gradle` 에 SonarQube 자격증명이
  평문으로 존재한다.
- **해결:** **값을 문서·로그·커밋·캡처에 복제하지 않는다.** 코드는 키 경로(`${aes.token}`)만 참조.

### 5.6 Windows 빌드 불가
- **증상:** `*** Windows is not support build`.
- **원인:** `build.gradle` 이 `wget` 으로 nexus `maven-metadata.xml` 을 받아 버전을 계산.
- **해결:** 빌드·검증은 Mac/Linux. Windows 에서는 컴파일 가능한 범위·정적 검토로 대체하고 그 사실을 보고한다.

---

## 6. 리팩터링 금지 목록

- On-premise 철자 4종(`OnPremise`·`Onpremise`·`OnPremiss`·`OnPromise`) 및 enum `ON_PREMISS` 일괄 개명 —
  참조가 광범위하게 깨진다. 검색 시에는 대소문자 무시 + `onpremis`/`onpromis` 두 철자를 함께 본다.
- 한글 클래스·메서드명(`상태`, `커넥트아이디_오류체크`, `요구사항_*_집계`) 영문화.
- 기존 저작권 주석 블록 제거.
- `esframework` 내부(`custom/client`, `factory`, `repository/common`) 임의 수정 —
  전 도메인이 의존한다. 바꿔야 하면 영향 범위를 먼저 보고한다.
- 요청 범위 밖 "개선" (YAGNI).

---

## 7. 리뷰 체크리스트

**DTO / VO**
- [ ] DTO 는 요청 전용, VO 는 응답 전용인가?
- [ ] `record` 를 쓰지 않았는가?
- [ ] 검색 요청 DTO 가 필요 시 `SearchRequestDTO` 를 상속하는가?

**주입 · 패턴**
- [ ] 생성자 주입(`@AllArgsConstructor`/`@RequiredArgsConstructor`)인가?
- [ ] Entity→VO 변환이 VO 내부 정적 팩토리로 캡슐화됐는가?
- [ ] 조건 분기가 있는 빌더를 변수로 분리했는가?
- [ ] 가드 절로 초기 검증했는가? 설명 변수를 썼는가?

**OpenSearch**
- [ ] `EsCommonRepositoryWrapper` 만 사용했는가? (클라이언트·`EsCommonRepository` 직접 접근 없음)
- [ ] **`recent` 포함 여부가 의도대로인가?**
- [ ] 멀티필드에 `.keyword`/`.text` 를 명시했는가? 단독 keyword 에 잘못 붙이지 않았는가?
- [ ] 쿼리 필드를 리터럴로 작성했는가? (상수화 금지)
- [ ] `includeFields` 가 `docs/almIssueEntity.md` 매핑에 있는 경로인가?
- [ ] alias 를 안 읽으면 `mainFieldAlias`/`subFieldAlias` 를 붙이지 않았는가?
- [ ] 전량 집계에 composite 를 썼는가?
- [ ] 새 엔티티면 `EntityClassConfig` 에 Wrapper Bean 을 등록했는가?

**통신**
- [ ] 모듈 간 호출이 Feign 인가? (`RestTemplate`/`WebClient` 직접 호출 없음)
- [ ] Feign 이 도메인 하위 `openfeign/` 에 있고 name 이 유일한가?
- [ ] 외부 ALM I/O 가 WebFlux + 429 재시도인가?
- [ ] ALM 분기가 해당 도메인의 방식(팩토리 또는 셀렉터)을 따르는가?
- [ ] 엔드포인트·JQL·인덱스명을 설정에서 가져오는가?

**공통**
- [ ] 횡단 관심사를 AOP 로 분리했는가?
- [ ] 에러가 `ErrorCode` + `ErrorControllerAdvice` 흐름을 따르는가?
- [ ] 인증정보를 AES256 으로 다루고 토큰 값을 노출하지 않았는가?
- [ ] Swagger `/engine-fire-api/swagger-ui/` 에 새 API 가 노출되는가?
- [ ] 요청 범위 밖 변경이 없는가?
