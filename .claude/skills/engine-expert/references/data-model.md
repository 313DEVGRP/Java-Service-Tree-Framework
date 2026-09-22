# 데이터 모델 — OpenSearch 인덱스

영속 계층은 전부 OpenSearch다. RDB·JPA·Flyway 마이그레이션이 없다.
**필드 매핑의 정본은 `docs/almIssueEntity.md` 의 Index Mapping** 이다. 쿼리를 쓰기 전에 반드시 연다.

---

## 1. 인덱스 전량 (엔티티 ↔ `@Document`)

| 엔티티 | `@Document(indexName)` | 비고 |
|--------|------------------------|------|
| `AlmIssueEntity` | `#{@jiraissue}` (`createIndex=false`) | 핵심. 롤링 + recent + `@ElasticSearchIndex` |
| `ServerInfoEntity` | `#{@serverinfo}` | ALM 서버 연결 정보(AES 암호화 필드) |
| `AtlassianServerInfoEntity` | `#{@serverinfo}` (`createIndex=false`) | Atlassian Admin 토큰 |
| `FluentdEntity` | `#{@fluentd}` (`createIndex=false`) | 롤링(`yyyyMMdd`) 로그 수집 |
| `WikiEntity` | `wiki` | recent + `@ElasticSearchIndex`. `/ai-search` 검색 대상 |
| `BbsEntity` | `bbs` | `@Setting(/es-settings/bbs-index-settings.json)` — ngram 분석기 |
| `PocEntity` | `arms_poc` | `@Setting(/es-settings/poc-index-settings.json)` |
| `BlogEntity` | `blog` | |
| `NewsletterEntity` | `newsletter` | |
| `HolidayEntity` | `holiday` | |
| `IndexStatusEntity` | `indexstatus` | 인덱스 작업 스냅샷 |

### 인덱스 베이스명은 설정 주입 — 리터럴 금지

`config/ElasticsearchIndexNameConfig`(`@RefreshScope`)가 `String` Bean 3개를 노출하고,
엔티티는 SpEL 로 참조한다.

| 설정 키 | Bean 이름 | 기본 베이스명 |
|---------|-----------|---------------|
| `arms-index-name.jiraissue` | `jiraissue()` | `jiraissue` |
| `arms-index-name.serverinfo` | `serverinfo()` | `serverinfo` |
| `arms-index-name.fluentd` | `fluentd()` | `fluentd` |

```java
@Document(indexName = "#{@jiraissue}", createIndex = false)   // ✓
@Document(indexName = "jiraissue")                            // ✗ 운영에서 베이스명이 바뀌면 깨진다
```

코드 어디서든 `"jiraissue"` 문자열을 직접 쓰지 않는다. 인덱스명이 필요하면
`esCommonRepositoryWrapper.indexAliasName()` 또는 위 Bean을 주입받는다.

---

## 2. 롤링 인덱스와 `recent`

```
논리 이슈 1건 ──┬─ jiraissue-2026-03-25  { recent_id:"srv_PRJ_PRJ-12", recent:false, status:"진행중" }
               ├─ jiraissue-2026-03-26  { recent_id:"srv_PRJ_PRJ-12", recent:false, status:"해결됨" }
               └─ jiraissue-2026-03-27  { recent_id:"srv_PRJ_PRJ-12", recent:true , status:"닫힘"  }
                                                                        ▲ 최신본은 항상 하나
```

| 애너테이션 | 대상 | 역할 |
|-----------|------|------|
| `@RecentId` | 필드 | 논리 키. `AlmIssueEntity.recentId` = `{jira_server_id}_{ProjectKey}_{key}`, `WikiEntity.wikiId` |
| `@Recent` | 필드 | 최신본 플래그(boolean) |
| `@RollingIndexName` | 메서드 | 인덱스 접미사 생성. 반환값이 `<base>-<접미사>` 로 붙음 |
| `@ElasticSearchIndex` | 클래스 | 이 클래스만 `save`/`saveAll` 이 recent 전환 로직을 탄다 |
| `@ElasticSearchCreatedDate` / `@ElasticSearchUpdateDate` | 필드 | 저장 시 자동 채움 |
| `@MonthBackup` / `@MonthMerge` | 클래스 | 월 단위 백업·머지 대상 표시 (`admin/indexdata`) |

```java
// AlmIssueEntity — Asia/Seoul(UTC+9) 기준 yyyy-MM-dd
@RollingIndexName
public String localDate() { ... }        // → jiraissue-2026-03-25

// FluentdEntity — yyyyMMdd
@RollingIndexName
public String indexName() { ... }        // → fluentd-20260325
```

`@RollingIndexName` 메서드는 **기본 생성자로 만든 인스턴스에서 호출**된다(리플렉션). 필드 상태에 의존하면 안 된다.

---

## 3. `AlmIssueEntity` — 요구사항 추적의 뼈대

### 3.1 연결·계층 필드 (이 저장소의 존재 이유)

| 필드 | 타입 | 의미 |
|------|------|------|
| `isReq` | boolean | A-RMS 가 만든 **요구사항 이슈**인지 |
| `cReqLink` | long | 요구사항 C_ID (Backend-Core 트리 노드 id) |
| `cReqStatusId` | long | 요구사항 상태 id |
| `parentReqKey` | keyword | 최상위 요구사항 이슈 key (요구사항 이슈 자신은 null) |
| `upperKey` | keyword | 직계 상위 이슈 key |
| `linkedIssues` | keyword[] | 연결 이슈들의 `recent_id` 목록 |
| `pdServiceId` | long | 제품·서비스 C_ID |
| `pdServiceVersions` | long[] | 제품 버전 C_ID 목록 |
| `linkedIssuePdServiceIds` / `linkedIssuePdServiceVersions` | long[] | 연결 이슈 전체의 제품·버전(자기 포함) |
| `issuetype.issuetype_hierarchyLevel` | long | **Sub-task: -1, Story/Task: 0, Epic: 1** |

집계에서 거의 항상 `pdServiceId` + `pdServiceVersions` + `isReq` 로 먼저 좁힌다.

### 3.2 중첩 객체 (모두 `properties`, 문자열 하위는 대부분 `text` + `.keyword` 멀티필드)

| 객체 | 대표 하위 필드 | 정적 중첩 클래스 |
|------|----------------|------------------|
| `project` | `project_id`, `project_key`, `project_name` | `Project` |
| `issuetype` | `issuetype_name`, `issuetype_subtask`(bool), `issuetype_hierarchyLevel`(long) | `IssueType` |
| `assignee` / `reporter` / `creator` | `*_accountId`, `*_displayName`, `*_emailAddress` | `Assignee`/`Reporter`/`Creator` |
| `priority` | `priority_id`, `priority_name`, `priority_isDefault` | `Priority` |
| `status` | `status_id`, `status_name`, `status_description` | `상태` (한글 클래스명) |
| `resolution` | `resolution_id`, `resolution_name`, `resolution_isDefault` | `Resolution` |
| `cReqProperty` | `cReqPriorityName`, `cReqDifficultyName`, `cReqStateName` (+ 각 `*Link` long) | `CReqProperty` |
| `worklogs` | 작업 로그 | `Worklogs`(+`Author`,`UpdateAuthor`) |

> `status` 의 중첩 클래스명이 **한글 `상태`** 다. 이 저장소의 실제 관례이므로 영문으로 바꾸지 않는다.

### 3.3 타입 주의 — `.keyword` 를 붙일 것과 붙이면 안 될 것

| 필드 | 타입 | 쿼리 표기 |
|------|------|-----------|
| `armsStateCategory` | 단독 keyword | `"armsStateCategory"` ← 접미사 **없음** |
| `key`, `recent_id`, `jira_server_id`, `parentReqKey`, `upperKey`, `linkedIssues` | 단독 keyword | 접미사 **없음** |
| `pdServiceId`, `pdServiceVersions`, `cReqLink`, `cReqStatusId`, `linkedIssuePdService*` | long | 접미사 없음 |
| `recent`, `isReq` | boolean | 접미사 없음 |
| `created`, `updated`, `resolutiondate`, `overallUpdatedDate`, `@timestamp` | date | `date_optional_time||epoch_millis` |
| `summary` | text + `.keyword` | 집계는 `"summary.keyword"` |
| `status.status_name`, `assignee.assignee_displayName`, `priority.priority_name` 등 | text + `.keyword` | 집계·필터는 `.keyword` 필수 |
| `labels`, `self`, `rawData` | 단독 text | 집계 불가 |
| `timespent` | integer | |
| `queries` | percolator | 저장형 쿼리 매칭용 |
| `etc` | auto | |

**정확한 구분은 항상 `docs/almIssueEntity.md` 에서 확인한다.** 여기 표는 자주 쓰는 것만 추린 것이다.

### 3.4 `@EqualsAndHashCode(exclude = {"recent","rawData"})`

중복 색인 방지 판정에 쓰인다(`references/esframework-query.md` §6).
필드를 추가·삭제하면 이 판정이 바뀐다는 점을 의식한다.

---

## 4. 인덱스 설정(`@Setting`)

`src/main/resources/es-settings/*.json` 에 분석기 설정을 둔다.

```java
@Document(indexName = "bbs")
@Setting(settingPath = "/es-settings/bbs-index-settings.json")   // ngram_analyzer 정의
public class BbsEntity implements BaseEntity { ... }
```

```java
@Field(type = FieldType.Text, name = "subject_name",
       analyzer = "ngram_analyzer", searchAnalyzer = "standard")
private String subjectName;
```

새 분석기가 필요하면 설정 json 을 추가하고 `@Setting` 으로 연결한다. 인덱스가 이미 있으면
분석기 변경은 **reindex 가 필요**하다(`admin/indexadmin`).

---

## 5. 수집 범위·버퍼 관련 설정 (모두 Global-Config 주입)

| 키 | 의미 |
|----|------|
| `alm.discovery.start-date` | 수집 시작일 (예: `2025-01-01`) |
| `alm.discovery.dateRange` | 청크 일수 (예: `30`) — `IssueSaveTemplate` 이 이 단위로 기간을 쪼개 순회 |
| `opensearch.buffer-limit-mb` | RestClient 응답 버퍼 상한 (기본 300MB, `largeBufferRequestOptions` Bean) |
| `backup.directory` / `backup.batch-size` | 인덱스 백업 (`admin/backup`) |
| `elasticsearch.url` | OpenSearch 접속 주소 |

> `docs/ai` 는 "대량 수집 시 Middle-Proxy Redis 버퍼(`redisbuffer` → `IssueBufferSender` → `MiddleProxyIssueBuffer`)"
> 를 설명하지만 **현재 코드에 그 패키지·클래스가 없다.** 기간 청크 순회(`IssueSaveTemplate`)가 실제 동작이다.
