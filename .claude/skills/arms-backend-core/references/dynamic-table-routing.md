# 제품별 동적 테이블 라우팅

이 저장소의 멀티테넌시는 스키마 분리도, 컬럼 분리도 아니고 **테이블 분리**다.
그리고 어떤 테이블을 칠지는 **HTTP 요청 경로**가 결정한다. 이해하지 않고 손대면 조용히 데이터가 섞인다.

관련 파일:
- `com/arms/egovframework/javaservice/treeframework/interceptor/RouteTableInterceptor.java`
- `com/arms/egovframework/javaservice/treeframework/interceptor/SessionUtil.java`
- `com/arms/config/RouteTableConfig.java`
- `com/arms/api/util/dynamicdbmaker/**` + `resources/com/arms/egovframework/mybatis/mapper/DynamicDBMakerDao.xml`
- `com/arms/api/util/communicate/internal/InternalService.java`

---

## 1. 대상 테이블 3종

제품(`pdService`)을 만들면 `DynamicDBMakerImpl.createSchema(pdServiceId)` 가 **한 번에 6개 테이블 + 9개 트리거**를 만든다:

| 접두사 | 예 | 용도 |
|--------|-----|------|
| `T_ARMS_REQADD_` | `T_ARMS_REQADD_12` (+ `_LOG`) | 요구사항 트리 |
| `T_ARMS_REQSTATUS_` | `T_ARMS_REQSTATUS_12` (+ `_LOG`) | ALM에서 수집된 요구사항 상태 |
| `T_ARMS_WIKI_` | `T_ARMS_WIKI_12` (+ `_LOG`) | 제품 위키 |

엔티티의 `@Table(name=...)` 은 **접미사 없는 템플릿 이름**(`T_ARMS_REQADD`)이다.
템플릿 테이블도 DB에 실제로 존재하지만(Flyway 생성), **운영 데이터는 거기 없다.**
라우팅이 실패하면 아무 예외 없이 그 빈 템플릿 테이블을 읽고 쓴다 — 이것이 전형적인 증상이다.

---

## 2. 치환이 성립하는 4가지 조건

```
[1] 컨트롤러 경로에 테이블명이 들어간다
    @RequestMapping("/arms/reqAdd")                     ← 클래스
    @RequestMapping("/{changeReqTableName}/getNode.do") ← 메서드
    요청 URL:  /arms/reqAdd/T_ARMS_REQADD_12/getNode.do
                              └ servletPath 에 "T_ARMS_REQADD_" 가 포함돼야 한다

[2] 서비스 호출 직전에 request attribute 를 심는다
    SessionUtil.setAttribute("getNode", changeReqTableName);

[3] RouteTableConfig 의 맵에 "마지막 경로 세그먼트 → attribute 키" 가 등록돼 있다
    reqAddRoute: map.put("getNode.do", "getNode");

[4] RouteTableInterceptor.onPrepareStatement 가 SQL 을 치환한다
    "... from T_ARMS_REQADD ..."  →  "... from T_ARMS_REQADD_12 ..."
```

`RouteTableInterceptor` 는 `context-hibernate.xml` 에서 `sessionFactory` 의 `entityInterceptor` 로 등록돼 있다.
치환은 `String.replaceAll("T_ARMS_REQADD", replaceTableName)` 단순 문자열 치환이다.

**5개 라우트 맵**이 있고, 각각 `servletPath` 에 어떤 문자열이 들어 있느냐로 선택된다:

| 조건 (`servletPath` 포함 문자열) | 사용하는 맵 빈 |
|---|---|
| `T_ARMS_REQADD_` | `reqAddRoute()` |
| `T_ARMS_REQSTATUS_` | `reqStatusRoute()` |
| `req-linked-issue` | `reqLinkedIssueRoute()` |
| `calculation` | `costRoute()` |
| `T_ARMS_WIKI_` | `wikiRoute()` |

---

## 3. 표준 컨트롤러 패턴

```java
@ResponseBody
@RequestMapping(value = {"/{changeReqTableName}/getMonitor.do"}, method = {RequestMethod.GET})
public ModelAndView getMonitor(@PathVariable("changeReqTableName") String changeReqTableName,
                               ModelMap model, HttpServletRequest request) throws Exception {

    SessionUtil.setAttribute("getMonitor", changeReqTableName);
    try {
        ReqAddEntity e = new ReqAddEntity();
        e.setOrder(Order.asc("c_position"));
        List<ReqAddEntity> list = reqAdd.getChildNodeWithoutPaging(e);

        ModelAndView mv = new ModelAndView("jsonView");
        mv.addObject("result", list);
        return mv;
    } finally {
        SessionUtil.removeAttribute("getMonitor");   // ★ 반드시 finally
    }
}
```

> 기존 코드 상당수는 `try/finally` 없이 정상 경로에서만 `removeAttribute` 를 호출한다.
> 예외가 나면 attribute 가 스레드에 남아 **같은 톰캣 스레드를 재사용하는 다음 요청이 남의 제품 테이블을 조회**한다.
> 실제로 이 사고가 있었고 `try/finally` 로 고쳤다(commit `035302ec`).
> **새로 쓰는 코드는 무조건 `try/finally` 로 감싼다.** 기존 코드를 고칠 때도 같은 파일 안이면 함께 정리한다.

### 새 엔드포인트를 만들 때 반드시 할 일

`RouteTableConfig` 의 해당 맵에 한 줄을 추가한다. **이 한 줄을 빼먹는 것이 1순위 실수다.**

```java
map.put("myNewEndpoint.do", "myNewEndpoint");   // 키 = 마지막 경로 세그먼트, 값 = attribute 키
```

`.do` 가 아닌 REST 스타일 경로도 같은 방식이다(`map.put("req-property-list", "req-property-list")`).
여러 엔드포인트가 같은 attribute 키를 공유해도 된다(`weeklyWorkload` · `monthlyWorkload` → `ptr-progress`).

---

## 4. HTTP 요청이 없는 곳에서는 loopback Feign 을 쓴다

`SessionUtil` 은 `RequestContextHolder` 기반이라 **Kafka 컨슈머 · `@Scheduled` · `@Async` 스레드에서는
`RuntimeException("requestAttributes is null")`** 이 난다.

그래서 이 저장소는 **자기 자신을 HTTP 로 다시 호출**한다:

```java
@FeignClient(name = "loopback", url = "http://127.0.0.1:31313")
public interface InternalService {
    @PostMapping("/arms/reqAdd/{changeReqTableName}/addNodeFromKafka.do")
    ResponseEntity<ReqAddVO> createFromKafka(@PathVariable String changeReqTableName, @RequestBody ReqAddDTO dto);
    ...
}
```

`ReqAddConsumerService.process()` 는 operation 별로 이 메서드들을 호출한다:

| Kafka operation | InternalService 메서드 | 라우트 키 |
|---|---|---|
| `ADD_NODE` | `createFromKafka` | `addNodeFromKafka.do` → `addNode` |
| `UPDATE_NODE` | `updateFromKafka` | `updateNodeFromKafka.do` → `updateNode` |
| `REMOVE_NODE` | `deleteFromKafka` | `removeNodeFromKafka.do` → `removeNode` |
| `MOVE_NODE` | `moveFromKafka` | `moveNodeFromKafka.do` → `moveNode` |
| `UPDATE_DATABASE` | `updateDataBaseFromKafka` | → `updateDataBase` |
| `UPDATE_DATE` | `updateDateFromKafka` | → `updateDate` |
| `UPDATE_REQADD_TITLE` | `updateReqAddTitleFromKafka` | → `updateReqAddTitleFromKafka` |
| `UPDATE_ALL_REQADD_STATE` | `updateAllReqAddStateFromKafka` | → `updateAllReqAddStateFromKafka` |
| `ADD_NODE_SKIP_ALM` | `addNodeAndThenSkipToCreateAlmIssueFromKafka` | → `addNode` |

**이 loopback 을 "비효율"이라며 서비스 직접 호출로 바꾸지 않는다.** 바꾸는 순간 라우팅이 죽고
전 제품 데이터가 템플릿 테이블 한 곳에 섞인다.

포트 `31313` 은 하드코딩돼 있다. 서버 포트를 바꾸면 이 클라이언트도 함께 바꿔야 한다
(실제 포트는 Config Server 의 `server.port`).

---

## 5. 스키마 진화 — Flyway 만으로는 부족하다

| 변경 대상 | 반영 수단 | 기존 제품 테이블에 적용되는가 |
|---|---|---|
| `T_ARMS_REQADD` / `_LOG` (템플릿) | `resources/com/arms/db/V*.sql` | — |
| 앞으로 생길 `T_ARMS_REQADD_<id>` | `DynamicDBMakerDao.xml` 의 `ddlOrgExecute` / `ddlLogExecute` | — |
| **이미 존재하는 `T_ARMS_REQADD_<id>`** | **없음** | ❌ **수동/별도 스크립트 필요** |

예: `V52__add_reqadd_req_def_id.sql` 은 `T_ARMS_REQADD` 와 `T_ARMS_REQADD_LOG` 만 `ALTER` 한다.
운영에 이미 있는 `T_ARMS_REQADD_1..N` 은 그대로다 → 엔티티에 필드를 추가하면
그 제품들에서 **`Unknown column` 오류**가 난다.

따라서 요구사항 계열 컬럼 추가 작업의 산출물에는 **항상 다음 4가지가 들어가야 한다**:

1. Flyway `V56__*.sql` (템플릿 본 테이블 + `_LOG`)
2. `DynamicDBMakerDao.xml` 의 `ddlOrgExecute` · `ddlLogExecute` 수정
3. **기존 제품 테이블 일괄 ALTER 계획** (예: `information_schema` 기반 동적 SQL 생성 스크립트) — 사용자에게 제시
4. 엔티티 + DTO 필드

### 트리거는 건드릴 필요가 없다

`TG_INSERT_/TG_UPDATE_/TG_DELETE_<table>` 은 `_LOG` 에 **트리 공통 컬럼 8개 + c_method/c_state/c_date** 만 복사한다.
도메인 컬럼은 로그에 남지 않는다(설계상). 그러니 컬럼 추가 시 트리거 수정은 불필요하다.

> 참고: `TG_INSERT_*` 는 `c_method` 를 `'update'`, `c_state` 를 `'변경이전데이터'` 로 기록한다
> (INSERT인데 'update'). 기존 동작이므로 로그를 해석할 때 감안하되, 요청 없이 고치지 않는다.

---

## 6. 증상 → 원인 대응표

| 증상 | 원인 |
|------|------|
| 데이터가 조회되지 않는다 / 빈 배열 | 라우팅 실패 → 빈 템플릿 테이블 조회. `RouteTableConfig` 등록 확인 |
| 다른 제품 데이터가 보인다 | 이전 요청의 attribute 잔류. `removeAttribute` 누락 |
| `SessionUtil :: getAttribute - requestAttributes is null` | HTTP 요청 스레드가 아님 → `InternalService` loopback 을 써야 함 |
| `Unknown column 'c_xxx'` | 기존 제품 테이블에 컬럼 미반영 (§5) |
| 저장은 되는데 목록에 안 보인다 | 저장/조회 엔드포인트 중 한쪽만 라우트 키가 등록됨 |
| 로그에 `RouteTableInterceptor :: replaceTableName - empty` | attribute 는 심었는데 값이 비어 있음(=PathVariable 누락) |

진단 로그: `RouteTableInterceptor` 는 `servletPath` 를 `log.info` 로, 치환 전후 SQL 을 `log.debug` 로 남긴다.
`logback-<profile>.xml` 에서 해당 패키지를 DEBUG 로 올리면 치환 결과를 눈으로 확인할 수 있다.
