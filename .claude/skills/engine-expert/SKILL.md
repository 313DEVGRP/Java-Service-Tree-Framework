---
name: engine-expert
description: >-
  A-RMS 수집·집계 엔진 저장소(Java-Service-Tree-Framework-Engine-Fire)의 작업 규약.
  Spring Boot 3.5.6 · Java 21 · OpenSearch(spring-data-opensearch) 기반이며
  Backend-Core(Boot 2.6 · Java 11 · JPA/MySQL) · Middle-Proxy(WebFlux 게이트웨이)와 규칙이 전혀 다르다.
  ALM(Jira Cloud/온프레미스 · Redmine) 이슈 수집 · OpenSearch 색인 · 요구사항 기준 집계(Time/Scope/Resource/Cost) ·
  대시보드/리포트 API · 인덱스 백업·복구·모니터링 · wiki 키워드 검색(/ai-search) 을 건드릴 때 반드시 먼저 읽을 것.
  esframework · EsCommonRepositoryWrapper · SimpleQuery · aggregateRecent · compositeAllHits · deepestList ·
  valueByName · countByName · NestedPath · Dimensions · MetricLeaves · CardinalityLeaves · SubGroupFieldDTO ·
  AlmIssueEntity · recent_id · rolling index(jiraissue-YYYY-MM-DD) · @RollingIndexName · @ElasticSearchIndex ·
  EntityClassConfig · ElasticsearchIndexNameConfig · IssueStrategyFactory · AlmSelector · Retryable429Exception ·
  auto-code 템플릿 · business-pattern · 정적 팩토리 · 조건부 빌더 · CommonResponse · ErrorCode ·
  "엔진", "engine-fire", "엔진파이어", "수집", "집계", "오픈서치", "일래스틱", "이슈 디스커버리",
  "대시보드 집계", "주간보고", "롤링3개월" 같은 요청도 여기서 시작한다.
  단, 같은 "집계·대시보드·요구사항·리포트" 라도 MySQL 트리(nested-set) 기반이면 arms-backend-core,
  RAG·LLM·벡터스토어면 ai-expert 다. 여기는 OpenSearch 인덱스를 읽고 쓰는 쪽이다.
  JPA·MyBatis·RestTemplate·WebClient 직접 호출·record 타입으로 작성하지 않는다 — 이 저장소는 OpenSearch 전용이다.
---

# A-RMS Engine-Fire 작업 규약

대상 저장소: `Java-Service-Tree-Framework-Engine-Fire/`
(워크스페이스 루트 `C:\DEV\Project\Java-Service-Tree-Framework` 하위, 중첩 git 저장소)

이 저장소는 A-RMS의 **수집(Collect)·집계(Statistics) 엔진**이다.
외부 ALM(Jira/Redmine)에서 이슈를 끌어와 OpenSearch에 색인하고, 그것을 **요구사항 관점으로 재해석**해
대시보드·리포트 데이터를 만든다. 화면도 RDB도 없다. **모든 영속은 OpenSearch 인덱스다.**

---

## 0. 30초 요약 — 반드시 먼저 각인할 것

| 항목 | 값 |
|------|----|
| 스택 | Spring Boot **3.5.6** · Spring Cloud **2025.0.1** · **Java 21** (Gradle toolchain) |
| 웹 모델 | Spring **MVC**(`@RestController`) — 단, **외부 ALM I/O만 WebFlux** |
| 영속 | **OpenSearch 전용** (`spring-data-opensearch` 1.7.1 / `opensearch-java` 2.7.0). RDB·JPA·MyBatis 없음 |
| 저장소 접근 | `esframework` 의 **`EsCommonRepositoryWrapper<E>`** 만. 클라이언트 직접 호출 금지 |
| 모듈 간 통신 | **OpenFeign**(hc5). `RestTemplate`·`WebClient` 직접 호출 금지 |
| 외부 ALM | Jira REST(`/rest/api/3`) · Redmine REST. 전략 패턴 + 429 재시도 |
| API 문서 | springdoc-openapi. Swagger UI `/engine-fire-api/swagger-ui/` |
| 포트·설정 | `33333`. 설정은 **Spring Cloud Config(Global-Config)가 주입** — 저장소 yml 은 4줄짜리 뼈대뿐 |
| 규모 | 자바 **701개**(`src/main/java`) + 테스트 15개, `@RestController` **43개** |

> 버전 사실이 의심되면 언제나 `build.gradle` 이 정본이다.
> 저장소 자체 하네스 문서 `docs/ai/` 가 보조 정본이지만 **일부가 낡았다** — §9 와 `references/pitfalls.md` 를 먼저 볼 것.

### 이 저장소에서 쓰면 안 되는 것

```
✗ JPA / MyBatis / @Transactional / RDB 엔티티      → ✓ OpenSearch @Document + EsCommonRepositoryWrapper
✗ EsCommonRepository 직접 주입                     → ✓ EsCommonRepositoryWrapper<E> (EntityClassConfig 의 @Bean)
✗ RestHighLevelClient / operations 직접 사용        → ✓ SimpleQuery + Wrapper 메서드
✗ RestTemplate / WebClient 로 모듈 호출             → ✓ @FeignClient (도메인 하위 openfeign/)
✗ record 타입                                      → ✓ Lombok DTO(요청) / VO(응답)
✗ 필드·세터 주입(@Autowired 필드)                   → ✓ 생성자 주입(@AllArgsConstructor / @RequiredArgsConstructor)
✗ 인덱스명·JQL·Jira 엔드포인트 리터럴 하드코딩        → ✓ 설정 주입 Bean / 설정 템플릿
✗ 집계 필드에 .keyword 생략                         → ✓ 멀티필드는 항상 타입 명시 (§5)
```

---

## 1. 먼저 "어느 흐름인지" 판별한다

경로를 잘못 짚으면 엉뚱한 패키지를 고친다. 요청은 네 갈래 중 하나다.

```
                    ┌─(A) 수집(Collect)  api/issue/{discovery,directfetch,almapi,priority,status,type,resolution,schedule,search}
                    │      외부 ALM → 변환 → OpenSearch 색인. WebFlux·전략 패턴 영역
Middle-Proxy :13131 │
   (게이트웨이) ────▶│─(B) 집계(Statistics)  api/{analysis,dashboard,detail_dashboard,report,kpi,requirement}
   Engine-Fire      │      OpenSearch 집계 쿼리 → VO. esframework 영역. 외부 ALM 호출 없음
      :33333        │
                    ├─(C) 운영·관리  api/admin/{backup,restore,indexadmin,indexstatus,monitoring,schedule,almissue,fluentd}
                    │      인덱스 백업·머지·reindex·삭제·헬스
                    │
                    └─(D) 자체 콘텐츠·연결  api/{bbs,blog,wiki,newsletter,poc,holidayadmin,account,serverinfo,almproject,atlassian}
                           + api/ai/search (AI 서비스가 호출하는 wiki 키워드 검색)
```

- **(A)와 (B)를 섞지 않는다.** 집계 서비스가 외부 ALM을 직접 부르면 안 되고, 수집 전략이 집계 VO를 만들면 안 된다.
- (B)는 거의 전부 `AlmIssueEntity` 인덱스 하나를 서로 다른 각도로 집계하는 코드다. 새 위젯 요청은
  **대개 새 인덱스가 아니라 새 집계 쿼리 + 새 VO** 로 끝난다.

도메인 지도 상세 → `references/domains.md`

---

## 2. 도메인 표준 구조와 신규 도메인 생성

모든 도메인은 `src/main/java/com/arms/api/<domain>/` 아래 같은 계층을 갖는다.

```
api/<domain>/
├── controller/          @RestController
├── service/             인터페이스 + Impl (같은 패키지)
├── model/dto/           요청(Request) 전용
├── model/vo/            응답(Response) 전용
├── model/entity/        (인덱스를 가지는 도메인만)
├── model/enums/         (필요 시)
├── strategy/            (외부 ALM 분기가 있는 도메인만)
└── openfeign/           (모듈 간 통신이 있는 도메인만)
```

### 신규 도메인은 반드시 2단계로 만든다

1. **템플릿 단계** — `rules/auto-code.md` 를 그대로 따른다. 입력은 `${domain}` 하나.
   Controller / Service / ServiceImpl / RequestDTO / VO 의 **빈 골격만** 만든다.
   메서드 본문·조건문·반복문·주석·추가 필드 **금지**, `return` 은 `List.of()` 같은 기본값만.
2. **구현 단계** — `rules/business-pattern.md` 의 결정 트리를 따라 로직을 채운다(§6).

> 1단계를 건너뛰고 바로 완성 코드를 쓰지 않는다. 이 저장소의 명시적 규약이다.

### 새 인덱스(엔티티)를 추가할 때 — 빠뜨리면 기동 시 터진다

```java
// 1) 엔티티: BaseEntity 구현 + @Document
@Document(indexName = "myindex")          // 설정 주입 대상이면 "#{@jiraissue}" 같은 SpEL Bean 참조
public class MyEntity implements BaseEntity { ... }

// 2) config/EntityClassConfig 에 Wrapper Bean 등록 ★ 필수
@Bean
public EsCommonRepositoryWrapper<MyEntity> myEntityWrapper() {
    return repositoryOf(MyEntity.class);
}

// 3) 서비스는 Wrapper 를 생성자 주입
private final EsCommonRepositoryWrapper<MyEntity> esCommonRepositoryWrapper;
```

`EntityClassConfig` 등록을 빠뜨리면 주입 대상이 없어 컨텍스트가 뜨지 않는다.

---

## 3. esframework — 저장소 접근의 유일한 통로

`com.arms.egovframework.javaservice.esframework` 는 이 저장소의 **핵심 자산**이다.
OpenSearch 쿼리 DSL을 직접 만들지 말고 이 계층을 쓴다.

```java
@Slf4j
@Service
@RequiredArgsConstructor
public class IssueStateServiceImpl implements IssueStateService {

    private final EsCommonRepositoryWrapper<AlmIssueEntity> esCommonRepositoryWrapper;

    @Override
    public IssueArmsStateCountVO selectIssueStateCountVO(Rolling3mDTO dto) {

        SimpleQuery<MainGroupDTO> query = aggregation(          // static import: SimpleQuery.aggregation
                AggregationRequestDTO.builder()
                        .mainField("status.status_name.keyword")  // 멀티필드 → .keyword 명시
                        .mainFieldAlias("stateName")              // valueByName/countByName 으로 읽을 때만 지정
                        .build()
        )
                .andTermQueryFilter("pdServiceId", dto.getPdServiceId())
                .andTermsQueryFilter("pdServiceVersions", dto.getPdServiceVersions())
                .andTermQueryFilter("isReq", Boolean.FALSE)
                .andRangeQueryFilter(RangeQueryFilter.of("@timestamp").betweenDate("now-3M/d", "now/d+1d"));

        DocumentAggregations aggs = esCommonRepositoryWrapper.aggregateRecent(query);   // recent=true 만

        for (DocumentBucket bucket : aggs.deepestList()) {        // 최하위 버킷만 평평하게
            String state = bucket.valueByName("stateName");       // 조상 버킷까지 alias 로 거슬러 조회
            Long count   = bucket.countByName("stateName");
            ...
        }
    }
}
```

### 프레임워크가 기동 시 강제하는 제약 (`RepositoryConfiguration`)

`ApplicationListener` 3종이 `spring.elasticsearch-repository.path` 패키지를 스캔해 **fail-fast** 로 막는다.

| 위반 | 에러 메시지 |
|------|------------|
| 일반(public) 클래스가 `EsCommonRepository` 를 필드로 보유 | `EsCommonRepository 타입을 변수로 가질 수 없습니다.` |
| 위 클래스가 메서드를 선언 | `공통저장소를 구현한 클래스는 변수로 사용 하실수 없습니다.` |
| `EsCommonRepository` 를 상속한 인터페이스가 메서드 선언 | `공통저장소를 상속한 인터페이스는 메소드를 가질수 없습니다.` |

→ 실무 규칙: **서비스에는 언제나 `EsCommonRepositoryWrapper<E>` 를 주입한다.**
저장소 인터페이스를 새로 만들 일이 생기면 메서드를 **하나도** 선언하지 않는다.

메서드 전량·선택 기준·집계 결과 읽는 법 → `references/esframework-query.md`

---

## 4. `recent` 와 롤링 인덱스 — 이 저장소 고유의 가장 큰 함정

`AlmIssueEntity` 는 같은 ALM 이슈의 **이력을 계속 쌓는다.** 같은 이슈가 여러 문서로 존재한다.

| 개념 | 의미 |
|------|------|
| `@RecentId` (`recent_id`) | 논리 키. `{jira_server_id}_{ProjectKey}_{key}` |
| `@Recent` (`recent`) | 이 문서가 그 논리 키의 **최신본인지** 여부(boolean) |
| `@RollingIndexName` | 저장 시 인덱스명 접미사를 만드는 메서드 → `jiraissue-2026-03-25` |
| `@ElasticSearchIndex` | 붙은 엔티티만 `save`/`saveAll` 이 recent 전환 로직을 탄다 (`AlmIssueEntity`, `WikiEntity`) |

```
질문: "현재 상태" 를 보는가, "이력 전체" 를 보는가?
├── 현재 상태 (대시보드·리포트·집계의 기본) → aggregateRecent* / findRecentHits / findAllRecentDocsBySearchAfter
└── 이력 전체 (추이·변경 이력)              → aggregate* / findHits / findAllDocsBySearchAfter
```

**`recent` 를 빼먹으면 집계가 조용히 과대 집계된다.** 에러가 나지 않으므로 리뷰에서 반드시 확인한다.
`recent` 를 직접 `andTermQueryFilter("recent", true)` 로 붙이지 말고 `*Recent*` 메서드를 쓴다
(프레임워크가 `@Recent` 필드명을 리플렉션으로 찾아 넣어준다).

---

## 5. OpenSearch 필드 표기 규칙 — 어기면 결과가 비거나 깨진다

```
✓ "status.status_name.keyword"          집계·필터·정확 일치 → .keyword
✓ multi_match 로 자연어 검색              유사도·자연어      → .text
✓ "armsStateCategory"                    단독 keyword 필드는 접미사 없음
✓ "key", "recent_id", "parentReqKey", "upperKey", "linkedIssues"   단독 keyword
✓ "pdServiceId", "cReqLink", "cReqStatusId"                        long
✗ "status.status_name"                   멀티필드인데 타입 생략 → 토큰 깨짐/빈 결과
✗ private static final String FIELD = "..."  쿼리 필드 상수화 금지 — 항상 리터럴
```

- 필드 존재 여부·타입의 **정본은 `docs/almIssueEntity.md` 의 Index Mapping**이다. 쿼리를 쓰기 전에 연다.
- 중첩은 점 표기법(`priority.priority_name`).
- `mainFieldAlias`/`subFieldAlias` 는 `valueByName()`/`countByName()` 으로 읽을 때만 붙인다. 안 읽으면 붙이지 않는다.

주요 필드·계층 구조·타입 주의 목록 → `references/data-model.md`

---

## 6. 비즈니스 패턴 (구현 단계 결정 트리)

```
VO 생성에 도메인 지식이 필요한가?
├── YES → 정적 팩토리 (VO 내부 static from/of/create 로 캡슐화)
└── NO
     └── 필드 계산 전에 조건 분기나 null 처리가 필요한가?
          ├── YES → 조건부 빌더 (빌더를 변수로 분리)
          └── NO  → 기본 빌더
```

- **Entity → VO 변환 로직을 Service 에 노출하지 않는다.** VO 내부 `static` 메서드로 옮긴다.
- 유효성은 **가드 절**로 초기에 `throw` (`Optional.ofNullable(...).orElseThrow(...)`). 정상 흐름은 하단.
- 복잡한 체이닝 결과는 **설명 변수**로 분리한다.
- 한 줄 체이닝 안에 삼항·`filter().findFirst()` 가 끼면 즉시 조건부 빌더로 전환.

전체 컨벤션(DTO/VO·주입·응답 봉투·에러·AOP·Swagger) → `references/conventions.md`

---

## 7. 외부 ALM 연동 — 전략 패턴 + WebFlux + 설정 외부화

ALM 종류는 `ServerType` 3종: `CLOUD`(클라우드) · `ON_PREMISS`(온프레미스) · `REDMINE_ON_PREMISS`(레드마인_온프레미스).

분기 방식이 **도메인마다 두 가지**라 먼저 확인한다.

| 방식 | 사용처 | 형태 |
|------|--------|------|
| 팩토리 | `issue/almapi`, `issue/discovery`, `issue/directfetch` | `*StrategyFactory.getStrategy(connectId)` → `Map<ServerType, *Strategy>` |
| 셀렉터 | `account` | 호출자가 전략 구현체를 넘김 → `AlmSelector.getAccount(strategy, connectId)` |

- 외부 ALM 호출은 **WebFlux(비동기·논블로킹)**. 429 는 `Retryable429Exception` + 재시도로 처리하고 **동기 호출로 우회하지 않는다.**
- **Jira 엔드포인트·JQL·수집 범위를 코드에 쓰지 않는다.** `jira.api.*`, `redmine.api.*`, `alm.discovery.*` 설정 템플릿을 조합한다.
- ALM 인증 정보는 `util/aes` 의 AES256 으로 다룬다. 토큰 **값**을 로그·문서·커밋에 복제하지 않는다(키 경로 `${aes.token}` 만 참조).
- **"On-premise" 철자가 네 가지**(`OnPremise`·`Onpremise`·`OnPremiss`·`OnPromise`)로 갈려 있다.
  클래스를 찾을 때 대소문자 무시 + 두 철자(`onpremis`/`onpromis`)를 함께 검색한다.
  **기존 것을 일괄 개명하지 않는다**(참조 깨짐).

수집 파이프라인·전략·컨버터 상세 → `references/alm-integration.md`

---

## 8. 모듈 간 통신 (Feign)

```java
@FeignClient(name = "backendCoreReportPerformance", url = "${arms.backend-core.url}")
public interface BackendCoreReportPerformance {
    @PostMapping("/arms/report/{tableName}/getNodesWhereInIds.do")
    List<PriorityValueVO> selectPriorityValueByTable(@PathVariable String tableName, @RequestBody List<Long> cIds);
}
```

- 위치는 **도메인 하위 `openfeign/`**. (`docs/ai` 가 말하는 `msa_communicate/` 는 2026-08-28 커밋 `762ca582` 에서 개명됨 — 더 이상 없다.)
- `@FeignClient(name=...)` 은 **전역 유일**해야 한다. 과거 중복으로 기동이 깨진 적이 있다(커밋 `4b19395f`).
- 대상 URL 은 설정 주입: `arms.backend-core.url`(:31313) · `arms.middle-proxy.url`(:13131).
- 스캔 범위는 `config/OpenFeignConfig` 의 `@EnableFeignClients({"com.arms.api"})`.
- 현재 Feign 인터페이스는 5개뿐이다 → `references/domains.md` §연동.

---

## 9. `docs/ai/` 는 보조 정본이지만 낡은 곳이 있다

저장소에 자체 하네스 문서 `docs/ai/01_project_overview ~ 13_deploy_runbook` 가 있다. 맥락 파악에 좋다.
다만 **코드와 어긋난 부분을 확인했다**(2026-09-22 기준):

| docs/ai 서술 | 실제 |
|--------------|------|
| Feign 은 `msa_communicate/` 에 둔다 | **`openfeign/`** 으로 개명됨 (커밋 `762ca582`) |
| `issue/almapi/redisbuffer` → `IssueBufferSender` → `MiddleProxyIssueBuffer` | 해당 패키지·클래스 **현재 없음** |
| 도메인 목록(`issue/*`, `util/*`) | 일부 누락·불일치 (`issue/discovery`·`issue/directfetch` 누락, `util/aes` 는 실재) |

→ **언제나 코드가 정본이다.** `docs/ai` 를 근거로 파일을 찾다 없으면 개명·삭제를 의심하고 `git log` 를 본다.
작업 후 변경은 `docs/ai/11_changelog`, 새 함정은 `docs/ai/12_known_issues` 에 남긴다.

---

## 10. 작업 전 체크리스트

1. `build.gradle` 로 버전 확인 (Java 21 / Boot 3.5.6 — Boot 2.x·`javax.*` 문법 금지, `jakarta.*` 사용).
2. 흐름 판별 (§1) → 고칠 패키지 확정.
3. 인덱스를 건드리면 `docs/almIssueEntity.md` 매핑부터 연다.
4. 집계라면 **`recent` 포함 여부를 먼저 결정**한다 (§4).
5. 새 도메인이면 `rules/auto-code.md` 템플릿 → `rules/business-pattern.md` 구현, 2단계 준수.
6. 새 엔티티면 `EntityClassConfig` 에 Wrapper Bean 등록.
7. 모듈 호출은 Feign, 외부 ALM 은 WebFlux + 전략 + 설정 템플릿.
8. 끝나고 `references/pitfalls.md` 의 리뷰 체크리스트로 자기검증.

> 빌드는 **Windows에서 안 된다.** `build.gradle` 이 `wget` 으로 nexus 메타데이터를 읽어 버전을 계산한다
> (Windows 에서는 `*** Windows is not support build` 출력). 검증은 Mac/Linux 또는 컴파일 가능한 범위에서.
> 상세 → `references/build-and-ops.md`

---

## 참조 문서

| 파일 | 내용 |
|------|------|
| `references/esframework-query.md` | Wrapper 메서드 전량 · SimpleQuery 조립 · 서브집계 4종 · 결과 읽기 · composite 순회 |
| `references/data-model.md` | 인덱스 목록 · AlmIssueEntity 필드/계층 · recent·롤링 인덱스 · 인덱스명 설정 Bean |
| `references/domains.md` | 도메인 지도 · 컨트롤러 경로 · 각 도메인의 역할과 진입점 |
| `references/alm-integration.md` | 수집 파이프라인 · 전략/팩토리 · 429 · AES · Feign 계약 · /ai-search |
| `references/conventions.md` | auto-code 템플릿 · 비즈니스 패턴 · 응답/에러 · AOP · Swagger · 네이밍 |
| `references/pitfalls.md` | 실제 확인된 함정 목록과 회피법 · 리뷰 체크리스트 |
| `references/build-and-ops.md` | 빌드 · 도커 · 설정 서버 · 인덱스 운영(백업·머지·reindex) · 테스트 |
