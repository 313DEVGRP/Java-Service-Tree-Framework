# 외부 ALM 연동 · 수집 파이프라인

---

## 1. ALM 종류 — `ServerType`

```java
public enum ServerType {
    CLOUD("클라우드"),
    ON_PREMISS("온프레미스"),
    REDMINE_ON_PREMISS("레드마인_온프레미스");

    public static ServerType typeValueOf(String name)   // 한글 문자열 → enum, 미지원이면 IllegalArgumentException
}
```

> **"On-premise" 표기가 네 가지로 갈려 있다.** 클래스를 찾을 때 한 철자만 검색하면 놓친다.
>
> | 표기 | 개수 | 예 |
> |------|------|-----|
> | `OnPremise*` (다수·정상) | 약 20개 | `OnPremiseJiraIssueStrategy`, `OnPremiseRedmineDiscoveryContext` |
> | `Onpremise*` (소문자 p) | 7개 | `OnpremiseJiraProjectStrategy`, `OnpremiseRedmineIssueTypeStrategy` |
> | `OnPremiss*` (VO 계열) | 4개 | `OnPremissJiraIssueVO`, `OnPremissRedmineVOCollection` |
> | `OnPromise*` (account 전략) | 2개 | `OnPromiseJiraAccountStrategy`, `OnPromiseRedmineAccountStrategy` |
>
> enum 상수는 `ON_PREMISS` / `REDMINE_ON_PREMISS` 다.
> **기존 이름을 일괄 개명하지 않는다.** 참조가 광범위하게 깨진다. 신규 클래스만 `OnPremise` 로 짓는다.
> 검색할 때는 `-iname "*onpremis*" -o -iname "*onpromis*"` 처럼 대소문자 무시 + 두 철자를 함께 본다.

---

## 2. 전략 분기 — 두 가지 방식이 공존한다

### 2.1 팩토리 방식 (권장 · 다수)

```java
@Component
public class IssueStrategyFactory {
    private final Map<ServerType, IssueStrategy> strategyMap;   // 스프링이 주입한 List<IssueStrategy> 로 구성

    public IssueStrategyFactory(ServerInfoService serverInfoService, List<IssueStrategy> strategies) {
        this.strategyMap = strategies.stream()
                .collect(Collectors.toMap(IssueStrategy::getServerType, Function.identity()));
    }

    public IssueStrategy getStrategy(String connectId) {
        ServerType type = serverInfoService.verifyAndGetServerType(connectId);
        ...
    }
}
```

- 전략 구현체는 `getServerType()` 으로 자기 타입을 신고한다.
- **새 전략을 추가하면 `@Component` 로 등록만 하면 자동 편입**된다. 팩토리를 수정할 필요 없다.
- 같은 `ServerType` 을 신고하는 구현체가 둘이면 `toMap` 이 기동 시 터진다.

사용처: `issue/almapi`(`IssueStrategyFactory`), `issue/discovery`(`IssueDiscoveryStrategyFactory`),
`issue/directfetch`(`AlmDirectFetchStrategyFactory`).

### 2.2 셀렉터 방식 (`account` 도메인)

```java
@Component
public class AlmSelector {
    public AlmAccount getAccount(AccountStrategy strategy, String connectId) { return strategy.getAccount(connectId); }
    public AlmAccount verifyAccount(AccountStrategy strategy, ServerInfoVO vo)  { ... }
}
```

호출자가 전략 구현체를 직접 고른다. `CloudJiraAccountStrategy` / `OnPromiseJiraAccountStrategy`(오타 표기 그대로) /
`OnPromiseRedmineAccountStrategy`.

`almproject` 은 또 다른 형태(`ProjectStrategy` + `ProjectStrategyImpl` + ALM별 구현)다.
**도메인을 건드리기 전에 그 도메인이 어느 방식인지 먼저 확인한다.**

---

## 3. 수집 파이프라인 (`issue/discovery`)

```
IssueDiscoveryController  /engine/jira
   │
   ▼
IssueDiscoveryService
   │
   ├── IssueDiscoveryStrategyFactory.getStrategy(connectId)
   │        └── {CloudJira,OnPremiseJira,OnPremiseRedmine}IssueDiscoveryStrategy
   │               ├── *Navigator      : 어디서부터 어떻게 탐색할지
   │               ├── *Paginator      : 페이지 순회 (Cloud Jira 는 nextPageToken / isLast)
   │               └── *KeyChangeTracker: 이슈 키 변경 추적
   │
   ├── traversal/  RootIssueExplorer · IssueTraversalQueue · IssueHierarchyTracer
   │               RequirementResolver · RequirementTracer      ← 요구사항 연결 계산
   │
   ├── converter/  *IssueToAlmIssueVOConverter  (ALM 원본 → AlmIssueVO)
   │               AlmIssueVOToEntityConverter  (VO → AlmIssueEntity, 요구사항/비요구사항 분리)
   │               AlmIssueParentLookup · IssueDateParser
   │
   └── IssueSaveTemplate
           ├── alm.discovery.start-date ~ endDate 를 dateRange(일) 단위 청크로 분할
           ├── 청크마다 전략 실행 → AlmIssueVOCollection
           └── esCommonRepositoryWrapper.saveAll(...)  → recent 전환 + 롤링 인덱스 색인
```

`IssueSaveTemplate` 의 핵심 계약:

```java
LocalDate startDate = LocalDate.parse(
        Optional.ofNullable(dto.getStartDate()).orElseGet(almDiscoveryDate::getStartDate), formatter);
// currentStart ~ endDate 를 dateRange 만큼씩 잘라 반복 호출
```

→ 수집 기간을 늘리면 **호출 횟수가 늘 뿐** 한 번에 거대한 요청이 나가지 않는다. 이 구조를 우회하지 않는다.

`IssueRecentStateManager` 는 수집 중 recent 상태 정합을 관리한다. 수집 경로에서 `save` 를 직접 부르기 전에
이 클래스를 먼저 본다.

---

## 4. Jira / Redmine REST — 설정 템플릿만 쓴다

**엔드포인트·JQL을 코드에 리터럴로 쓰지 않는다.** Global-Config 가 주입하는 템플릿을 조합한다.

| 항목 | 값/템플릿 (설정) |
|------|------------------|
| Jira API base | `/rest/api/3` |
| 검색 | `${jira.api.base}/search/jql` |
| 페이지 크기 | `jira.api.parameter.maxResults` (25) |
| 수집 필드 | `project,issuetype,creator,reporter,assignee,labels,priority,status,resolution,resolutiondate,created,updated,worklogs,timespent,summary,subtasks,issuelinks,parent` |
| packet-size | 10MB |
| JQL — 전체 | `issue={이슈키}` |
| JQL — 서브태스크 | `parent={이슈키}` |
| JQL — 연결이슈 | `issue in linkedIssues({이슈키})` |
| JQL — 증분 | `(updated >= startOfDay(-1) and updated < startOfDay())` |
| createmeta | `${jira.api.endpoint.issue.base}/createmeta/{프로젝트}/issuetypes/{이슈유형}` |
| Redmine | `/projects/{아이디}.json`, `/issues/{아이디}.json`, `/trackers.json?tracker_id=`, `/issue_statuses.json?status_id=`, `/enumerations/issue_priorities.json` |

관련 유틸: `util/alm/JiraApi`, `JiraUtil`, `RedmineApi`, `RedmineUtil`, `AlmDiscoveryDate`.
저장소 루트에 `RedmineApi.md`, `RedminePrompt.md` 참고 문서가 있다.

---

## 5. WebFlux + 429 재시도

- 외부 ALM I/O는 **WebFlux(비동기·논블로킹)** 로 한다. 목적은 I/O 효율 + rate limit 대응.
- 클라이언트는 `config/WebClientBuilder`.
- 429 응답은 `util/exception/Retryable429Exception(delaySeconds)` 을 던지고 재시도 경로를 탄다.

```java
public class Retryable429Exception extends RuntimeException {
    private final long delaySeconds;
    public long getDelaySeconds() { ... }
}
```

**금지:** 429 를 피하려고 동기 호출·`Thread.sleep`·무한 재시도로 바꾸는 것.
`delaySeconds` 를 존중하는 재시도 연산자를 쓴다.

> 주의: 이 저장소에서 WebFlux 는 **외부 ALM I/O 전용**이다. 컨트롤러는 MVC 다.
> 컨트롤러 반환 타입을 `Mono`/`Flux` 로 바꾸지 않는다(Middle-Proxy 와 혼동 금지).

---

## 6. 인증정보 암호화 (`util/aes`)

- `ServerInfoEntity.passwordOrToken`, `atlassianApiKey` 등은 AES256 으로 저장한다.
- 키는 설정 `${aes.token}`. **토큰 값 자체를 로그·문서·커밋·캡처에 복제하지 않는다.**
- 사용처: `serverinfo/service/ServerInfoServiceImpl`, `atlassian/service/AtlassianAdminServiceImpl`.

---

## 7. `/ai-search` — AI 서비스에 제공하는 wiki 검색

Engine-Fire 는 RAG 파이프라인의 **데이터 제공자**일 뿐이다. Spring AI·Ollama·VectorStore·임베딩은
**별도 모듈 `Java-Service-Tree-Framework-AI`** 소관이고, 이 저장소 `build.gradle` 에 Spring AI 의존성이 없다.

| 항목 | 값 |
|------|----|
| 경로 | `POST /ai-search/keyword` |
| 요청 | `AiKeywordSearchRequestDTO { keywords: ["a","b"] }` — 비면 400 |
| 응답 | `List<AiSearchDocumentVO> { id, keyword, title, content, score, metadata }` |
| 구현 | `WikiSearchServiceImpl` — `findRecentHits` + `withMultiMatchQueryShouldAtLeastOne(MultiMatchQueryShould::defaultFuzzy, ...)` |
| 상한 | 코드 상수 `MAX_RESULTS`(현재 **2**) |
| 실패 처리 | 예외 시 **빈 목록 반환** (검색 실패가 AI 파이프라인을 막지 않도록) |

주의점 두 가지:

1. `AiSearchDocumentVO` 는 AI 서비스의 `SearchEngineDocumentVO` 와 **필드 1:1 일치**해야 한다.
   한쪽만 바꾸면 역직렬화가 깨진다.
2. `MAX_RESULTS` 를 단독으로 올리지 않는다. AI 서비스의 LLM 컨텍스트 예산(`num_ctx`)과 함께 검토한다.

`title` 은 `WikiEntity.wikiId`, `content` 는 `WikiEntity.contents` 로 매핑된다는 점도 기억한다
(필드명이 직관과 다르다).

---

## 8. Slack / DWR 알림

```java
@SlackSendAlarm(messageOnStart = "...", messageOnEnd = "...")   // util/aspect/SlackSendAdvice 가 처리
public void someLongJob() { ... }
```

- 채널은 `SlackProperty.Channel`(예: `engine`).
- `ErrorControllerAdvice.onException` 이 잡히지 않은 예외를 Slack `engine` 채널로 보낸다.
- `@DwrSendAlarm` 은 `DwrBackendCoreClient` 를 통해 Backend-Core 알림으로 나간다.
- 알림 메시지에 토큰·인증정보를 넣지 않는다.
