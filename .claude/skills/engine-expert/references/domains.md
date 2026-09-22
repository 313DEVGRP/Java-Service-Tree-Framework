# 도메인 지도 — 어디를 고쳐야 하는가

`src/main/java/com/arms/api/<domain>/`. 컨트롤러 43개. 아래는 실제 `@RequestMapping` 값 기준이다.

> **경로 접두가 일관되지 않다.** `/engine/*` 이 다수지만 `/{connectId}/jira/*`, `/report/*`,
> `/alm/account`, `/holiday`, `/anonymous/bbs`, `/ai-search`, `/atlassian/admin` 도 있다.
> 새 도메인은 `rules/auto-code.md` 기본형(`/<domain>`)이지만, **기존 그룹을 확장할 때는 그 그룹의 접두를 따른다.**

---

## A. 수집 (Collect) — 외부 ALM → OpenSearch

| 도메인 | 경로 | 역할 |
|--------|------|------|
| `issue/discovery` | `/engine/jira` | **수집 본체.** 이슈 탐색·계층 추적·변환·색인 |
| `issue/directfetch` | `/engine/issue-direct` | 단건/지정 이슈 즉시 조회 (색인 없이 원본 반환) |
| `issue/almapi` | `/{connectId}/jira/issue` | ALM 이슈 생성·수정·상태변경·삭제 (A-RMS → ALM 쓰기) |
| `issue/schedule` | `/engine/jira` | 수집 스케줄 트리거 |
| `issue/{priority,status,type,resolution}` | `/{connectId}/jira/issue*` | ALM 메타데이터 조회 |
| `issue/search` | — | 색인된 이슈 검색(`AlmIssueSearchImpl`) |
| `account` | `/alm/account` | ALM 계정 검증·조회 (전략 패턴) |
| `almproject` | `/{connectId}/jira/project` | ALM 프로젝트 조회 (전략 패턴) |
| `serverinfo` | `/engine/serverInfo` | ALM 서버 연결정보 CRUD (AES 암호화) |
| `atlassian` | `/atlassian/admin` | Atlassian Admin API — 디렉터리·사용자 동기화 |

`issue/discovery` 내부 구조(가장 복잡한 패키지):

```
issue/discovery/
├── controller/   IssueDiscoveryController
├── strategy/     IssueDiscoveryStrategyFactory + {cloudjira,jira,redmine}/ 각 Strategy·Navigator·Paginator·KeyChangeTracker
├── traversal/    IssueNavigator · IssueTraversalQueue · IssueHierarchyTracer
│                 RequirementResolver · RequirementTracer · RootIssueExplorer
├── converter/    {CloudJira,OnPremiseJira,OnPremiseRedmine}IssueToAlmIssueVOConverter
│                 AlmIssueVOToEntityConverter · AlmIssueParentLookup · IssueDateParser
├── context/      DiscoveryContext + ALM별 구현 (수집 세션 상태·LRU 캐시)
├── service/      IssueDiscoveryService · IssueSaveTemplate · IssueRecentStateManager
└── model/        dto · vo (ALM별 원본 VO + Collection)
```

수집 흐름 상세 → `alm-integration.md`

---

## B. 집계 (Statistics) — OpenSearch → 차트/리포트 VO

| 도메인 | 경로 | 역할 |
|--------|------|------|
| `analysis/time` | `/engine/analysis-time` | Time 축 — 일정 준수·지연 |
| `analysis/scope` | `/engine/analysis-scope` | Scope 축 — 요구사항 달성률·범위 (트리바·서클패킹·네트워크) |
| `analysis/resource` | `/engine/analysis-resource` | Resource 축 — 담당자 부하 (트리맵·워드클라우드·생키·파이·스택바) |
| `analysis/cost` | `/engine/analysis-cost` | Cost 축 — 공수·급여 기반 비용 |
| `analysis/topmenu` | `/engine/analysis-top-menu` | 상단 요약 지표 |
| `dashboard` | `/engine/dashboard` | 메인 대시보드 집계 |
| `detail_dashboard` | `/engine/detail-dashboard` | 상세 대시보드 |
| `kpi` | `/engine/kpi` | KPI 집계 |
| `requirement` | `/engine` | 요구사항 기준 조회·집계 |
| `report/fulldata` | `/engine/report` | 전체 데이터 리포트 |
| `report/weekly` | `/engine/weekly/business-report`, `/report/personal-performance` | 주간 업무보고 · 개인 성과 |
| `report/rolling3m` | `/report/rolling3m`, `/assignees/rolling3m` | 최근 3개월 롤링 리포트 (상태·자원·요구사항분포·팀평균) |
| `report/ptr` | `/engine/portfolio-track-record` | 포트폴리오 트랙 레코드 |
| `search_engine` | `/engine/search` | 통합 검색 |
| `backoffice/information/timeoff` | `/engine/backoffice/timeoff` | 휴가 집계 |

**집계 도메인의 공통 형태**

```java
@Service @RequiredArgsConstructor @Slf4j
public class XxxImpl implements Xxx {
    private final EsCommonRepositoryWrapper<AlmIssueEntity> esCommonRepositoryWrapper;
    // SimpleQuery.aggregation(...) → aggregateRecent* → deepestList() → VO 정적 팩토리
}
```

가장 큰 파일들(참고용 idiom 출처): `AnalysisResourceImpl`(2345줄), `AnalysisScopeImpl`(1595),
`WeeklyServiceImpl`(1456), `RequirementServiceImpl`(907), `AnalysisTimeImpl`(861).
**짧고 깨끗한 표준 예시는 `report/rolling3m/service/IssueStateServiceImpl`** — 새 집계를 쓸 때 이것을 본뜬다.

---

## C. 운영·관리 (admin)

| 도메인 | 경로 | 역할 |
|--------|------|------|
| `admin/backup` | `/engine/index/backup` | 인덱스 백업 (`backup.directory`, batch) |
| `admin/restore` | `/engine/index/restore` | 백업 복구 |
| `admin/indexadmin` | `/engine/index/es-index` | 인덱스 생성·삭제·reindex·머지 |
| `admin/indexstatus` | `/engine/index/index-status` | 인덱스 작업 상태 스냅샷 (`@IndexStatusSnapShot` AOP) |
| `admin/almissue` | `/engine/index/alm-issue` | 이슈 인덱스 관리 |
| `admin/fluentd` | `/engine/index/fluentd` | fluentd 로그 인덱스 |
| `admin/monitoring` | `/engine/admin/monitoring` | OpenSearch 클러스터 모니터링 |
| `admin/schedule` | `/engine/admin/schedule` | 백업 스케줄 트리거 |
| `admin/indexdata` | — | `@MonthBackup` / `@MonthMerge` 애너테이션 정의 |

> **`@Scheduled` 는 이 저장소에 없다.** "스케줄"은 외부(또는 다른 모듈)가 REST 로 트리거하는 방식이다.
> `Application` 은 `@EnableAsync` + `@EnableAspectJAutoProxy` 만 걸려 있다.

---

## D. 자체 콘텐츠

| 도메인 | 경로 | 인덱스 |
|--------|------|--------|
| `bbs` | `/anonymous/bbs` | `bbs` (ngram 분석기, 비밀글·답글 path/indent 트리) |
| `blog` | `/engine/blog` | `blog` |
| `wiki` | `/engine/wiki` | `wiki` (recent 이력 관리) |
| `newsletter` | `/engine/newsletter` | `newsletter` |
| `poc` | `/engine/poc` | `arms_poc` |
| `holidayadmin` | `/holiday` | `holiday` |
| `ai/search` | `/ai-search` | `wiki` 검색 제공 (AI 서비스가 호출) |

---

## E. 공통 유틸 (`api/util`)

| 패키지 | 내용 |
|--------|------|
| `util/aes` | `AES256`, `AES256Decryption`, `AESProperty` — ALM 인증정보 암복호 |
| `util/alm` | `JiraApi`, `JiraUtil`, `RedmineApi`, `RedmineUtil`, `AtlassianApi`, `AtlassianUtil`, `AlmDiscoveryDate` |
| `util/aspect` | `LoggingAdvice`, `SlackSendAdvice`/`@SlackSendAlarm`, `DwrSendAdvice`/`@DwrSendAlarm`, `AppProperty` |
| `util/errors` | `ErrorCode`(enum, 한글 메시지), `ErrorControllerAdvice`, `ErrorLogUtil` |
| `util/response` | `CommonResponse` (`ApiResult<T>` / `ApiError`) |
| `util/exception` | `Retryable429Exception` |
| `util/openfeign` | `DwrBackendCoreClient` |
| `util/slack` | `SlackNotificationService`, `SlackProperty.Channel` |
| `util/env`, `util/model`, `util/log_converter` | 환경·공용 DTO·로그 변환 |

---

## F. 모듈 간 연동 (Feign 인터페이스 — 현재 5개 전부)

| 인터페이스 | 위치 | 대상 | 용도 |
|-----------|------|------|------|
| `BackendCoreReportPerformance` | `serverinfo/openfeign` | Backend-Core | 리포트용 트리 노드·우선순위·마감통계·요구사항 상태 |
| `BackendCoreJiraServer` | `serverinfo/openfeign` | Backend-Core | Jira 서버 모니터 정보 |
| `MiddleProxyArmsStateCategory` | `issue/almapi/openfeign` | Middle-Proxy | `GET /mapping/category` — A-RMS 상태 카테고리 매핑 |
| `MiddleProxyAtlassian` | `atlassian/openfeign` | Middle-Proxy | Atlassian 디렉터리 사용자 저장 |
| `DwrBackendCoreClient` | `util/openfeign` | Backend-Core | `POST /arms/alarm/send-message` — 실시간 알림 |

새 Feign 을 만들 때: **도메인 하위 `openfeign/` 패키지**, `@FeignClient(name=...)` 전역 유일,
`url = "${arms.backend-core.url}"` 또는 `"${arms.middle-proxy.url}"`.

---

## G. `config` 패키지

| 파일 | 역할 |
|------|------|
| `OpensearchClientConfig` | `RestHighLevelClient` + `CustomOpenSearchRestTemplate`. timeout 60s, keepAlive 180s, `RefreshPolicy.IMMEDIATE` |
| `ElasticsearchProperties` | `elasticsearch.url` (`@RefreshScope`) |
| `ElasticsearchIndexNameConfig` | 인덱스 베이스명 String Bean 3종 (`@RefreshScope`) |
| `EntityClassConfig` | **엔티티별 `EsCommonRepositoryWrapper` Bean 등록처** — 새 엔티티는 여기 추가 |
| `CustomElasticsearchHealthIndicator` | actuator 헬스 |
| `OpenFeignConfig` / `HttpClient5FeignConfig` | Feign |
| `WebClientBuilder` | 외부 ALM WebFlux 클라이언트 |
| `OpenApiConfig` / `SwaggerUIConfiguration` | springdoc. UI 포워딩 `/engine-fire-api/swagger-ui/` |
| `SlackConfig` | Slack 알림 |
| `IndexBackupConfig` / `CaptchaConfig` | 백업 · 캡차 |
