# `arms/js/common.js` 공통 API 레퍼런스

`arms/js/common.js` (약 2,950줄) 는 arms 와 backoffice 가 **함께 쓰는** 단일 공통 허브다.
(`backoffice/template.html` 도 `../arms/js/common.js` 를 로드한다.)
여기 있는 함수를 다시 구현하지 말고 그대로 호출한다. 줄 번호는 조사 시점 기준의 위치 힌트이며,
호출 전에 실제 파일에서 시그니처를 한 번 확인하는 편이 안전하다.

## 목차
1. 부트스트랩 / 라이프사이클
2. 플러그인 로더
3. 인증 · 권한 · 사용자
4. 테이블 (DataTables)
5. 트리 (jstree)
6. 알림 · 로딩 UI
7. 국제화(i18n)
8. 도움말 모달 · 투어 가이드
9. 쿠키 · 테마 · URL 파라미터
10. 날짜 · 문자열 · 값 유틸
11. 요구사항 상태(ARMS State) 헬퍼
12. 내비게이션 / 외부 링크

---

## 1. 부트스트랩 / 라이프사이클

| 함수 | 설명 |
|------|------|
| `$(function(){...})` (common.js:26) | URL 에 `landing_` 이 있으면 인증 없이 `runScript()`, 아니면 `authUserCheck()`. |
| `runScript()` | 레이아웃 조립 + `ajax_setup()` + `includeLayout(page)` + `$.getScript("js/{page}.js")` → `execDocReady()` → `menu_setting()`. `?withoutLayer=1` 쿼리를 주면 헤더/사이드바를 숨긴 임베드 모드가 된다. |
| `includeLayout(page)` | `[data-include]` 를 스캔해 조각을 `$.load()`. `content-header`/`content-container` 는 `html/{page}/...` 로, 나머지는 `html/template/...`(landing·detail·backoffice 변형)으로 해석된다. |
| `includeContents($container)` | 조각 안에 중첩된 `[data-include]` 를 추가로 로드하고 **해당 요소를 결과로 치환**한다. 큰 화면을 섹션 파일로 쪼갤 때 쓴다. |
| `menu_setting()` | `permissions`(Keycloak realm roles)로 상단/사이드 메뉴 표시를 분기. `ROLE_USER` → dashboard·detail, `ROLE_MANAGER` → +product·alm·requirement, `ROLE_ADMIN` → +analysis·report. |
| `setSideMenu("sidebar_menu_a", "sidebar_menu_a_b", ...)` | 가변 인자. 해당 id 에 `active` + 색상(`#a4c6ff`)·굵기를 입힌다. 1초 뒤 `.spinner` 문구를 기본 문구로 교체하는 부수효과가 있다. |
| `widgsterWrapper()` | lightblue4 위젯의 fullscreen 동작 패치. |
| `로드_완료_이후_실행_함수()` | 플러그인 로드 완료 후 공통 후처리(테마·슬림스크롤 등). `loadPluginGroupsParallelAndSequential()` 이 자동 호출하므로 직접 부르지 않는다. |
| `톱니바퀴_초기설정()` | 우측 상단 설정(사이드바 위치·테마) 팝오버 초기화. |
| `triggerChartsResize()` | 등록된 차트들에 resize 전파. 탭 전환·레이아웃 변경 후 호출. |

## 2. 플러그인 로더

```javascript
loadPluginGroupsParallelAndSequential([
	["a.js", "b.js"],   // 그룹 내부는 순차 (의존 순서)
	["c.css", "c.js"]   // 그룹끼리는 병렬
]).then(function () { /* 초기화 */ });
```

| 함수 | 설명 |
|------|------|
| `loadPlugin(url)` | Promise. `.js` 는 `$.ajax({dataType:"script", cache:true})`, 그 외는 `<link rel=stylesheet>` 로 head 에 주입. 로드 직전 `.spinner` 에 "OO 다운로드 중" 문구를 쓴다(완료 후 지우지 않음 → 페이지에서 `$(".spinner").empty()` 필요). |
| `loadPluginGroupSequentially(group)` | 배열을 순차 로드. |
| `loadPluginGroupsParallelAndSequential(groups)` | 그룹 병렬 + 그룹 내부 순차. 완료 시 `로드_완료_이후_실행_함수()` 실행 후 resolve. |

> CSS 도 같은 배열에 섞어 넣는다. 확장자로 분기하므로 별도 처리가 필요 없다.

## 3. 인증 · 권한 · 사용자

| 함수 / 전역 | 설명 |
|------------|------|
| `authUserCheck()` | `GET /auth-user/me` (timeout 7313, `global:false`). 200 이면 전역 변수 채우고 `$.authorization(userID, page)` 통과 시 `runScript()`. 401 → `jError` + `/oauth2/authorization/middle-proxy` 리다이렉트. 403 → `jError`. |
| `getUserInfo()` | `GET /auth-user/search-user/{userName}` → `userApplicationRoles`, `userAttributes`, `userGroups`, `userRealmRoles` 등 채움. |
| `우측_상단_사용자_정보_설정()` | 헤더 사용자 영역 렌더. |
| 전역 변수 | `userName`(preferred_username) · `userID`(sub) · `userEmail` · `fullName` · `userJti` · `permissions`(realm roles 배열) · `currentLanguagePack` |

> `userEmail` 은 Keycloak `email` 이며, KPI 계열 API 가 담당자 식별자로 쓴다(`assigneeEmailAddress`).

## 4. 테이블 (DataTables 1.10.16)

```javascript
dataTable_build(
	jquerySelector,   // "#req_table"
	ajaxUrl,          // "/auth-user/api/arms/reqAdd/T_X/getMonitor.do"
	jsonRoot,         // 응답에서 배열이 있는 키. 루트 배열이면 ""
	columnList,       // [{ data:"c_id", title:"ID", defaultContent:"-" }, ...]
	rowsGroupList,    // 행 그룹 컬럼 인덱스 배열. 안 쓰면 []
	columnDefList,    // [{ targets:"_all", render: fn }, ...]
	selectList,       // DataTables Select 옵션 객체. 안 쓰면 {}
	orderList,        // [[1, "asc"]]
	buttonList,       // Buttons 확장 정의. 안 쓰면 []
	isServerSide,     // dataTable_build 내부에서 항상 false 로 덮임
	scrollY,          // "400px" 등 (선택)
	data,             // isAjax=false 일 때 넘길 로컬 배열 (선택)
	isAjax,           // 기본 true
	errorMode         // 기본 true
);
```

- **서버사이드 페이징이 필요하면 `dataTable_extendBuild(...)` 를 직접 호출**한다.
  `dataTable_build` 는 같은 인자를 받되 `isServerSide` 를 내부에서 `false` 로 고정한다.
- 내부 설정: `destroy: true`(재빌드 허용), `processing: true`, `responsive: false`,
  `rowsGroup`, `select`, `buttons`, `scrollY` 를 인자로 그대로 전달.
- `initComplete` / `drawCallback` / 행 클릭에서 **페이지 전역 함수를 호출**한다:
  `dataTableCallBack(settings, json)` · `dataTableDrawCallback(tableInfo)` ·
  `dataTableClick(tempDataTable, selectedData)`.
  **선언이 없으면 ReferenceError** 가 나므로 빈 본문이라도 반드시 선언한다.
- 행 클릭 핸들러는 `click.dtBuild` / `page.dt.dtBuild` / `length.dt.dtBuild` 네임스페이스로
  bind 되고 재빌드 시 해당 네임스페이스만 `off` 된다. 페이지가 직접 거는 핸들러는
  **다른 네임스페이스**를 쓰면 안전하게 공존한다.
- 반환값은 DataTables API 인스턴스다. 갱신은 `table.ajax.reload()` · `table.clear().rows.add(rows).draw()`.

### 새 테이블 래퍼 `$.fn.table` (`arms/js/common/table_new.js`)
백오피스와 일부 arms 화면(`reqStatus`, `analysisResource`, `pocReqRegister`)이 쓰는 상위 래퍼다.
플러그인 그룹에 `"../arms/js/common/table_new.js"` 를 추가해야 로드된다.

```javascript
var t = $("#user_table").table({ columns: [...], ... });
t.table.ajax.reload();          // 내부 DataTables 인스턴스
$("#user_table").table().getSelectedData();
```
주요 메서드: `dataTableBuild` · `clear` · `addRows` · `reDraw` · `reSize` · `empty` ·
`removeRows(cb)` · `getSelectedData` · `getColumns` · `getData($row)` · `getDatas`.
훅: `onToggleCheckAll` · `onToggleCheckbox` · `onRowClick`.

### 기타
- `hideDetail_Datagrid()` — 열려 있는 child row 접기.
- `scrollPos` (전역) — 페이지 이동/표시개수 변경 직후에만 스크롤 복원. `null` 이면 복원 안 함.

## 5. 트리 (jstree v.pre1.0)

```javascript
jsTreeBuild(jQueryElementID, serviceNameForURL, serviceNameForSyncURL, slimScrollHeight);
// 예) jsTreeBuild("#req_tree", "/auth-user/api/arms/reqAdd/T_X", undefined, "545px");
```

- `serviceNameForSyncURL` 생략 시 `serviceNameForURL` 을 그대로 쓴다.
- 서버 규약(nested-set 트리) — **백엔드 엔드포인트가 이 이름을 그대로 제공해야 한다**:
  - 조회: `{serviceUrl}/getChildNode.do`, `{serviceUrl}/searchNode.do`
  - 변경: `{syncUrl}/addNode.do`, `/removeNode.do`, `/alterNode.do`, `/alterNodeType.do`, `/moveNode.do`
- 노드 타입은 `rel` 속성: `drive`(루트) · `folder` · `default`(리프).
- 플러그인 셋: `themes, json_data, ui, crrm, dnd, search, types` (테마 `lightblue4`).
- 노드 선택 시 페이지 전역 `jsTreeClick(selectedNode)` 를 호출한다(jQuery 객체가 인자).
  `selectedNode.attr("id")` 는 `node_{c_id}` 형식, `selectedNode.attr("rel")` 이 타입.
- 로드 완료 후 `slimscroll({height: slimScrollHeight || "545px"})` 이 걸린다.
- 성능 때문에 자동 `open_all` 은 꺼져 있다.

## 6. 알림 · 로딩 UI

| 함수 | 설명 |
|------|------|
| `jSuccess(msg[, opts])` / `jError(msg[, opts])` / `jNotify(msg[, opts])` | jNotify 2.1 토스트. **`alert()` 대신 항상 이것을 쓴다.** 옵션 예: `{autoHide:true, TimeShown:3000, HorizontalPosition:"center", VerticalPosition:"top"}` |
| `ajax_setup()` | 전역 AJAX 훅 등록. `ajaxStart` → `.loader` 표시, `ajaxError` → 401 리다이렉트 / 403·500 `jError`, `ajaxComplete` → `Ladda.stopAll()`, `ajaxStop` → `.loader` 숨김. **페이지에서 401/403/500 을 중복 처리하지 않는다.** |
| `topbarConfig()` / `topbar.show()` / `topbar.hide()` | 상단 프로그레스 바. |
| `laddaBtnSetting([".btn_a", ".btn_b"])` | 버튼에 `ladda-button` 클래스 + 진행 스피너 바인딩. |
| `makeSlimScroll(target)` | 슬림 스크롤 적용. |
| `rightBottomTopForwardIcon()` / `supportBubble()` | 맨 위로 아이콘 / ARMS AI 말풍선. |
| `$(".loader")`, `$(".spinner")` | 전역 로딩 오버레이와 그 안의 문구 영역. 플러그인 로드 후 `$(".spinner").empty()` 를 권장. |

## 7. 국제화(i18n) — i18next 아님, 자체 구현

| 함수 | 설명 |
|------|------|
| `loadLocale()` | 쿠키 `locale` 을 읽어 `setLocale()` 호출. |
| `changeLocale(locale)` | 허용값 `["ko","ja","en"]`. 허용 밖이면 `ko`. 쿠키 저장 후 재바인딩. |
| `setLocale(locale = "ko")` | Global-Config(`/auth-anon/yml/language-config/packs/language/{locale}`) 우선, 실패 시 로컬 `arms/locales/{ko,en,jp}.json` 폴백. |
| `bindLocaleText(locales)` | `document.querySelectorAll("[data-locale]")` 를 순회해 텍스트/placeholder 주입. |
| `flattenObject(obj, parentKey)` | JSON 을 `nav.product.p` 형태의 점 표기 키로 평탄화. → **마크업의 `data-locale` 값이 이 점 표기 키**다. |
| `sanitizeHTML(content)` | 허용 태그만 남긴다: `span, small, strong, p, b, ul, li, br`. |
| `isPlaceholder(tag)` / `isIncludeHTMLTag(content)` | 내부 판별. |

마크업 사용:
```html
<span data-locale="nav.requirement.q">요구 관리</span>
<input data-locale="form.search.placeholder" placeholder="검색어" />
```
> ⚠️ 코드 로케일은 `ja` 인데 폴백 파일명은 `jp.json` 이다. `ja` 선택 시 `/arms/locales/ja.json` 404.
> 반면 도움말 JSON 폴더는 `help/full-page/ja/` 로 `ja` 를 쓴다. 두 규칙이 다르다.

## 8. 도움말 모달 · 투어 가이드

- 마크업: `data-help="{key}" data-help-type="page"` (섹션 도움말은 `data-help-type` 생략)
- `setPageManual(key)` → `./help/full-page/{locale}/{key}.json`
- `setSectionManual(key)` → `./help/page-section/{locale}/{key}.json`
- JSON 구조: `{ meta:{l1,l2,version,lastUpdated}, flow, help_body:{title,desc}, video:{label,path}, sections }`
- 오버레이는 `#quickstart_overlay` / `#content_area`, 닫기는 `.mn-close`.
- 투어: `tourGuideStart()` · `getTourGuideMode()` / `setTourGuideMode(mode)` · `checkTourGuideMode()` ·
  `tourGuideEventListener()`. 스텝 정의는 `arms/js/common/tourGuide/tgGroup.js`, API 는 `tgApi.js`.

## 9. 쿠키 · 테마 · URL 파라미터

| 함수 | 설명 |
|------|------|
| `getCookie(cname)` | 쿠키 조회. |
| `setCookie(name, value, exp = 1, paths = ["/arms", "/backoffice"])` | **두 영역에 동시에 심는 것이 기본값**이다. 도메인/경로 전제가 깨지면 로그인 세션이 끊긴다. |
| `setTheme("dark" \| "light")` / `loadTheme()` | 테마 쿠키 적용. `afterSetDarkTheme()` / `afterSetLightTheme()` 훅. 라이트 테마는 `body.light-theme` 로 CSS 분기. |
| `getPageName()` | `?page=` 값. |
| `getParameter(param)` / `setParameter(param, value)` | 쿼리스트링 읽기/쓰기. |
| `checkMobileDevice()` | UA 기반 모바일 판별. |
| `UrlBuilder` (class) | `new UrlBuilder().setBaseUrl(u).addQueryParam(k,v).build()`. |

## 10. 날짜 · 문자열 · 값 유틸

| 함수 | 설명 |
|------|------|
| `isEmpty(value)` / `isExist(value)` | null·undefined·빈문자·빈배열 판정. 조건문에서 이 둘을 쓰는 것이 이 코드베이스의 관례. |
| `dateFormat(timestamp)` / `dateFormatSlash(timestamp)` | `YYYY-MM-DD` / `YYYY/MM/DD` 계열 포맷. |
| `getToday()` | 오늘 날짜 문자열. |
| `timestampToDatepicker(timestamp)` | datepicker 입력값 형식으로 변환. |
| `isValidShortFormat(s)` / `isValidISOFormat(s)` / `parseDateString(s)` | 날짜 문자열 파싱·검증. |
| `getStrLimit(inputStr, limitCnt)` | 말줄임(`...`) 처리. |
| `maxValue(arr)` / `minValue(arr)` | 배열 최대/최소. |
| `getJsonForPrototype(url, bindTemplate)` | 프로토타입용 JSON 로드 후 템플릿 바인딩. |

## 11. 요구사항 상태(ARMS State) 헬퍼

모두 Promise 를 반환한다.

| 함수 | 엔드포인트 / 동작 |
|------|------------------|
| `get_arms_state_category_list()` | `GET /auth-user/api/arms/reqStateCategory/getNodesWithoutRoot.do` → `data.result` |
| `get_arms_req_state_list()` | `GET /auth-user/api/arms/reqState/getReqStateListFilter.do` |
| `req_state_setting(element, is_disabled)` | 상태 목록을 조회해 해당 엘리먼트에 라디오 버튼 그룹 렌더 |
| `binding_state_list(container_id, req_state_list, is_disabled)` | `#{container_id}` 에 상태 라벨/인풋 생성. 비활성화 시 `btn btn-disabled font12` |

## 12. 내비게이션 / 외부 링크

| 함수 | 설명 |
|------|------|
| `goToTemplatePage(pageName)` | `template.html?page={pageName}` 이동. |
| `goToTemplatePageWithSearchString(pageName, searchString)` | 검색어를 함께 전달. |
| `targetLink(path)` | 현재 컨텍스트(detail 모드 등)를 유지한 채 페이지 이동. 사이드바 메뉴가 이 함수를 쓴다. |
| `gnuboardLink(bo_table)` / `gnuboardList(param)` / `gnuboardIndex()` | 커뮤니티(gnuboard) 연동 링크. |
| `검색_이벤트_트리거()` | `#search_form_collapse` 등 검색 폼 4종에 focus/click/submit 이벤트 위임 등록. |

---

## 함께 보는 공통 모듈

| 경로 | 용도 |
|------|------|
| `arms/js/common/table_new.js` | `$.fn.table` 테이블 래퍼 (§4) |
| `arms/js/common/colorPalette.js` | 차트 색상 팔레트 |
| `arms/js/common/chart/eCharts/*.js` | ECharts 프리셋 (donut · radar · 수평 막대 · nightingale · treemap 등) |
| `arms/js/common/chart/d3/*.js` | D3 프리셋 (sankey · donut · timeline · combination) |
| `arms/js/common/dwrChat.js` | DWR 기반 AI 채팅 연동 (`dwr_login()`) |
| `arms/js/common/jspreadsheet/*` | 엑셀형 시트 헬퍼 |
| `arms/js/common/swiperHelper.js` | 랜딩 캐러셀 |
| `arms/js/common/tourGuide/{tgApi,tgGroup}.js` | 투어 가이드 |
| `arms/js/common/api/topMenuCoreApi.js` | 상단 메뉴용 API 헬퍼 |
