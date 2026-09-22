# result.md — claude-main / REQ-FRONTEND-FUNC-01

> §6 변환 코드 전문은 워커 제출 원본 그대로 같은 폴더의 `extract_api_calls.py` (926줄) 에 보관.
> 본문에서는 경로로만 참조한다 (전사 과정의 훼손 방지).

## 1. 추출 범위

대상: `Java-Service-Tree-Framework-Frontend-Web/arms/js` · `backoffice/js` — **js 169개 전수**(하위 디렉토리 포함).

### 1-1. 호출 프리미티브 실측 (마스킹 후 = 문자열·주석·정규식리터럴 내부 제외)

| 패턴 | grep 원시 | 실제 호출 지점 | 차이 사유 |
|---|---|---|---|
| `$.ajax(` | 409 | **404** | 5건이 주석 문장 |
| `$.get(` | 9 | **9** | — |
| `$.post(` | 1 | **1** | — |
| `$.getJSON(` | 2 | **2** | — |
| `fetch(` | 8 | **8** | — |
| 소계 | | **424** | |

> brief 의 `$.get 30` 은 `$.getJavascript`(5) · `$.getStylesheet`(9) · `$.getScript`(4) · `$.getJSON`(2) 를 포함한 느슨한 계수. 앞 3종은 정적 js/css 로더이므로 REST 대상이 아니다. 따라서 **448 → 424** 가 프리미티브 정본. `$.getJSON` 2건은 REST 가 아닌 정적 help JSON 이지만 호출 지점으로 포함했다.

### 1-2. 프리미티브 밖의 ajax config 지점 (추가 34건)

프리미티브 span 밖에 있는 `url:` 프로퍼티 36건 중, **key 경로에 `ajax` 가 있거나** enclosing callee 가 `fileupload`·`select2`·`ajaxPromise`·`fetchCached` 인 34건. 이들은 실제 네트워크 호출이다.

| 유형 | 건수 | 예 |
|---|---|---|
| `TopMenuCore.ajaxPromise({url:…})` (프로젝트 래퍼) | 12 | `arms/js/dashboard/api/dashboardApi.js` |
| DataTables / 테이블 플러그인 `ajax.url` | 8 | `backoffice/js/securityRole.js:188` |
| select2 `ajax.url: function(params)` | 6 | `arms/js/reqAdd.js:1131` |
| jQuery File Upload `url:` | 6 | `arms/js/pdService.js:482` |
| jsTree `json_data.ajax.url` / `search.ajax.url` | 3 | `arms/js/mapping.js:482` |
| `fetchCached(key,{url:…})` | 1 | `arms/js/aiSupport.js:1157` |

제외 2건 (API 아님): `arms/js/landing_blog.js:180` = `navigator.share({url})`, `arms/js/common/showdown/showdown.js:4047` = 번들 라이브러리 내부 데이터 객체.

**호출 지점 총계 = 424 + 34 = 458.**

## 2. 컬럼 스펙 (확정)

`menuname,area,jsfile,line,httpMethod,apiurl,callPattern,note`

| 컬럼 | 값 |
|---|---|
| `menuname` | 네비게이션의 메뉴 라벨. 미연결은 사유 라벨(§4) |
| `area` | `arms` \| `backoffice` |
| `jsfile` | 저장소 루트 기준 상대경로 (`arms/js/reqAdd.js`) |
| `line` | 호출 지점 시작 라인 (1-base) |
| `httpMethod` | `GET`/`POST`/`PUT`/`DELETE`/`PATCH`/`HEAD`. 분기형은 `POST\|PUT` |
| `apiurl` | 복원된 완성형 URL. 런타임 값은 `{name}` |
| `callPattern` | `$.ajax` · `$.get` · `fetch` · `select2(ajax)` · `ajaxPromise(url)` · `$.ajax via jsTreeBuild(arg2)` 등 |
| `note` | 복원 근거 / 정규화 사실 / 제약 |

인코딩 `utf-8-sig`(Excel 한글), 정렬 `area → jsfile → line → apiurl`.

## 3. URL 복원 규칙

기계 복원 (스캐너):

1. **소스 마스킹** — 문자열·주석·**정규식 리터럴**·템플릿 리터럴(중첩 `${}` 포함)을 코드와 분리. 정규식 리터럴 처리가 없으면 `arms/js/common.js:1695` 의 정규식 리터럴이 파서를 무너뜨려 그 이후 `$.ajax` 6건을 통째로 놓친다(실측 확인).
2. **문자열 연결** — 최상위 `+` 로 분할, 리터럴은 그대로, 런타임 식은 `{name}`.
   `name` 유도: `$("#selected_pdService").val()`→`selected_pdService`, `getCookie("locale")`→`locale`, `$target.attr("id")`→`id`, `encodeURIComponent(x)`→`x`, `a.b.c`→`c`.
3. **템플릿 리터럴** — `${expr}` → `{name}`.
4. **식별자 추적**
   - url 전체가 식별자면 앞쪽 대입을 가까운 순으로 시도, `/` 를 포함하는 첫 결과 채택.
   - 연결 피연산자면 감싼 블록 안의 대입들을 **모두 분기로 전개**(≤4). 빈 문자열 / 공백 포함 값(가드 문구)은 버린다.
   - 함수 파라미터 기본값(`function f(locale="ko")`)은 대입으로 보지 않는다.
5. **UrlBuilder 체인** — `new UrlBuilder().setBaseUrl(X)…build()` → X. `addQueryParam` 키는 note 로.
6. **삼항 전개** — `("a"?"/x":"/y")` → 2행.
7. **공통 빌더(디스패처) 호출부 인자 대입** — `dataTable_build`→`dataTable_extendBuild`(2단 체인), `jsTreeBuild`, `jira_server_request_create_or_update`, `handleStreamResponse`. URL 이 빌더 파라미터면 **호출부(caller) 파일:라인에 행을 만들고** 빌더 라인은 행을 만들지 않는다(중복 방지). `note` 에 `common.js:1799 dataTable_extendBuild->dataTable_build 경유` 로 출처 기록. `ajaxUrl=""` 인 클라이언트사이드 테이블 18건은 호출 없음이므로 행 삭제.
8. **같은 파일 함수 파라미터 전개** — `{X}` 가 감싼 함수의 파라미터면 같은 파일 호출부의 **리터럴 인자만** 대입(≤6). 식별자 인자가 섞여 있으면 일반형 `{X}` 행도 함께 남긴다.
9. **말미 정규화** — `/`·`?`·`&` 로 끝나면 제거하고 note 에 명시. 해당 2건(`securityGroup.js:421` `/auth-admin/realms/`, `systemInfo.js:270` `…/org-link/`)은 백엔드 카탈로그(`tasks/req-backend-func-01/artifacts/backend-core_endpoints_flat.csv` #286 `/admin/arms/backoffice/system-info/getSystemInfo/org-link`)와 대조해 슬래시 없는 형태가 맞음을 확인.

수작업 dict(근거 주석 포함) — 기계로 안 되는 17개 지점. 배열 인덱싱(`batch_url_list` 8개), `$targets` 배열 3원소(accessControl), `getVectorApiUrl()` 2분기, `url +=` 조건 분기(securityRole/securityUser), jiraServer 분기 변수 4곳, 래퍼 디스패치 지점 2곳(행 삭제).

### 복원 불가 4건 (모두 REST 아님 / 미사용 — 사유 명시)

| 파일:라인 | 값 | 사유 |
|---|---|---|
| `arms/js/adms/editor-operation.js:136` | `imgSrc.data` | draw.io 이미지의 data/blob URL 재요청 |
| `arms/js/common.js:619` | `loadPlugin(url)` | `dataType:"script"` 정적 플러그인 로더 (`reference/` 하위 js·css) |
| `arms/js/common.js:1068` | `ajaxGet(url)` | `getJsonForPrototype` 전용 유틸 — 저장소 내 호출부 없음 |
| `arms/js/common.js:1958` | `ajax_sample()` | 문서용 샘플 함수. url 값이 `"요청을 보낼 URL"` 설명문 |

→ `apiurl` 은 `UNRESOLVED:<표현식>` 으로 채운다(공란 아님, `/` 로 끝나지 않음).

## 4. 메뉴 매핑

- arms: `arms/html/template/page-navigation.html` — `page=` 링크 **30종**, `<a>` 텍스트를 메뉴명으로 사용.
- **backoffice 메뉴 정의 위치 = `backoffice/html/template/page-sidebar.html`** (미해결 이슈 해소) — `page=` 링크 **16종**.
- 라우팅 `template.html?page={page}` ↔ `js/{page}.js` 1:1. 하위 디렉토리 js 는 첫 세그먼트를 page 로 본다(`arms/js/reportSWOT/reqAddList.js` → `reportSWOT`).

사유 라벨 (공란 없음):

| 라벨 | 대상 | 행수 |
|---|---|---|
| `[공통모듈] common` | `js/common.js`, `js/common/**`, `js/util/**` | 22 |
| `[공통모듈] analysis (4개 분석메뉴 공용)` | `js/analysis/**` | 3 |
| `[랜딩·인증면제] landing_*` | 랜딩/마케팅 (네비 밖) | 41 (9종) |
| `[상세 읽기전용] detail_*` | `detail.html` 셸 | 32 (6종) |
| `[메뉴미연결·페이지존재] <page>` | `html/{page}` 는 있으나 링크 없음 — `kpi` · `reportKPI` · `reportWeekly` · `searchEngine` · `mailReportConfig` | 42 |
| `[메뉴미연결·공용모듈] <page>` | html 디렉토리도 없음 | 0 |

메뉴 라벨 63종 (네비 링크 46 + 사유 라벨 17).

## 5. 예상 행수 (스크래치패드 드라이런 실측)

```
rows=540  files=169  trailing-slash=0  blank=0  unresolved=4
stats: {'prim': 402, 'config': 30, 'manual': 17, 'dispatch': 9, 'clientside': 18}
```

| 지표 | 값 |
|---|---|
| CSV 행 | **540** |
| distinct apiurl | 382 |
| 호출 지점 | 458 (= prim 402 + config 30 + manual 17 + dispatch 9) |
| area | arms 418 / backoffice 122 |
| 호출이 있는 js 파일 | 81 / 169 |
| httpMethod | GET 315 · POST 141 · PUT 49 · DELETE 29 · HEAD 2 · PATCH 1 · 분기형 2 · 미해결 1 |
| URL prefix | `/auth-user` 399 · `/auth-admin` 94 · `/auth-anon` 37 · 기타 10 |
| **말미 `/` 행** | **0** |
| **필수 3컬럼 공란** | **0** |

행 > 지점인 이유: 분기 전개(삼항·배열·조건 대입)와 디스패처 호출부 전개.

## 6. 변환 코드

- 표준 라이브러리만 사용, 저장소는 읽기 전용, 출력 경로가 코드에 박혀 있음.
- 전문: `tasks/req-frontend-func-01/workers/claude-main/extract_api_calls.py` (워커 제출 원본 926줄)
- 실행: `python3 tasks/req-frontend-func-01/workers/claude-main/extract_api_calls.py`
  → `tasks/req-frontend-func-01/artifacts/frontend-web_api-calls_flat.csv` 생성 + 검증 통계 stdout.

## 7. Verification Checklist

Orchestrator 가 실행할 항목. 1~2번은 스크립트가 자체 출력한다.

- [ ] `python3 extract_api_calls.py` 종료코드 0, stdout 이 `rows=540  files=169  trailing-slash=0  blank=0  unresolved=4` 와 일치
- [ ] `tasks/req-frontend-func-01/artifacts/frontend-web_api-calls_flat.csv` 존재, 헤더 = `menuname,area,jsfile,line,httpMethod,apiurl,callPattern,note`
- [ ] 말미 `/` 행 0건
- [ ] 필수 3컬럼(`menuname`·`jsfile`·`apiurl`) 공란 0건
- [ ] `area` 가 `arms`·`backoffice` 양쪽 모두 존재 (arms 418 / backoffice 122)
- [ ] `UNRESOLVED` 로 시작하는 `apiurl` 이 4건이고 모두 `note` 에 사유가 있음
- [ ] 스크립트가 대상 저장소를 수정하지 않았음 — `git -C Java-Service-Tree-Framework-Frontend-Web status --porcelain` 이 비어 있음
- [ ] 표본 대조 (소스 직접 확인) — 아래 5행
      `arms/js/pdService.js:1085` → `/auth-user/api/arms/pdServiceDetail/deleteNode.do/{selectedDetailId}` POST
      `arms/js/reqGantt.js:408` → `/auth-user/api/arms/reqAddStatePure/T_ARMS_REQADD_{selectId}/monthlyProgressRate` GET
      `backoffice/js/kafkaAdmin.js` → `/auth-user/api/kafka/REQADD-DLT/list` (상수 2개 연결)
      `arms/js/reqAdd.js:427` → `…/reqAdd/sync/T_ARMS_REQADD_{selected_pdService}/alterNode.do` (jsTreeBuild 경유)
      `arms/js/searchEngine.js:188` → `/auth-user/search/engine/search/{almIssue|log|wiki}` 3행

## 8. Issues / Caveats

1. **brief 의 448건은 느슨한 grep 계수.** 정본은 프리미티브 424 + 플러그인/래퍼 config 34 = **458 지점**. `$.getJavascript`·`$.getStylesheet`·`$.getScript`(총 18건)는 정적 자원 로더라 제외했다. 이 판정을 바꾸려면 알려달라.
2. **범위를 프리미티브 4종 밖으로 넓혔다.** jsTree·DataTables·select2·fileupload·프로젝트 래퍼(`ajaxPromise`/`fetchCached`)의 `url:` 34곳을 넣지 않으면 `/auth-user/api/arms/analysis/top-menu/*`, `/auth-admin/realms/master/users` 등 실사용 엔드포인트가 통째로 빠진다. `callPattern` 으로 구분 가능하니 필요하면 필터링해서 쓰면 된다.
3. **공통 빌더 경유 행의 파일·라인은 호출부(caller) 기준이다.** `dataTable_build` 26행 · `jsTreeBuild` 18행이 여기 해당하며 `note` 에 `common.js:<line> … 경유` 로 원지점을 적었다. 메뉴 단위 집계를 맞추기 위한 선택이며, 빌더 내부 라인(`common.js:1799`, `1326`, `1370`, `1451`, `1472`, `1487`, `1506`, `1524`)에는 행을 만들지 않았다.
4. **`ajaxUrl=""` 인 클라이언트사이드 DataTable 18건은 행에서 제외**했다(네트워크 호출 없음). 예: `backoffice/js/esMonitoring.js:182`, `arms/js/reqGantt.js:569`.
5. **정적 자원 요청 3건이 CSV 에 남아 있다** — `arms/js/common.js:130`·`343` (`./help/full-page/{locale}/{help}.json`), `backoffice/js/scheduleConfig/host.js:11` (`html/generalconfig/content-container.html`). `/` 로 시작하지 않으므로 REST 목록에서 걸러내려면 `apiurl NOT LIKE '/%'` 로 배제하면 된다.
6. **`arms/js/detail.js:91` 의 복원값은 `…/reqAdd/T_ARMS_REQADD_/getDetail.do?…` 로 테이블 ID 자리가 비어 있다.** 오탈자가 아니라 소스가 `var tableName = "T_ARMS_REQADD_";` 로 상수 문자열만 넣기 때문이다(파일:라인 88). 사실만 기록했고 판단은 하지 않았다.
7. **`httpMethod` 분기형 2행**(`POST|PUT`)이 있다 — `landing_blogEditor.js:248` 은 url 도 2행으로 갈라져 있어 메서드 짝을 자동으로 맞추지 못했다. 나머지 1건(`common.js:1958`)은 샘플 함수라 `{type}`.
8. **backoffice 메뉴 정의 위치 확인 완료** = `backoffice/html/template/page-sidebar.html` (16 링크). `backoffice/html/` 아래 `appearance`·`dynamicConfig`·`mailReportConfig`·`securityGroup` 등 20개 디렉토리 중 사이드바에 없는 것은 `[메뉴미연결·페이지존재]` 라벨로 구분했다.
9. **저장소 무수정 확인.** 읽기만 했고 산출물은 스크래치패드에만 만들었다. `tasks/` 및 대상 저장소에는 아무것도 쓰지 않았다.
