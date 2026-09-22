---
name: arms-frontend-web
description: >-
  A-RMS 프론트엔드 저장소(Java-Service-Tree-Framework-Frontend-Web)의 화면 작업 규약.
  arms/ · backoffice/ 영역의 jQuery + Bootstrap 3 + lightblue4 멀티페이지 앱에서
  화면을 새로 만들거나 고칠 때, template.html?page= 라우팅 · execDocReady() 진입점 ·
  common.js 공통 빌더(dataTable_build · jsTreeBuild · setLocale · jNotify) ·
  reference/ 번들 라이브러리 · 게이트웨이 AJAX 계약을 이 규약대로 따르게 한다.
  content-container.html / content-header.html / js/{page}.js 를 건드리거나,
  DataTables · jstree · ECharts · select2 · multiple-select · jSpreadsheet 를 붙이거나,
  /auth-user · /auth-admin 엔드포인트를 연동하거나, i18n(data-locale) · 상태 색상 ·
  버튼 색상 규칙이 나오면 반드시 이 스킬을 먼저 읽을 것. "프론트 화면", "퍼블리싱",
  "arms 화면", "백오피스 화면", "요구사항 목록 화면", "대시보드 위젯" 같은 요청도 대상이다.
  React · Vue · TypeScript 로 새로 만들지 않는다 — 이 저장소는 전부 바닐라 JS다.
---

# A-RMS Frontend-Web 작업 규약

대상 저장소: `Java-Service-Tree-Framework-Frontend-Web/`
(워크스페이스 루트 `C:\DEV\Project\Java-Service-Tree-Framework` 하위)

이 저장소는 **트랜스파일·번들러가 없는 브라우저 직접 실행 앱**이다. `<script>` 로 올라간
전역 함수들이 서로를 이름으로 호출하는 구조라, 규약을 어기면 빌드 에러가 아니라
**런타임에 조용히 깨진다.** 아래 계약을 먼저 파악하고 손대는 것이 이 저장소에서
가장 비용이 싼 길이다.

---

## 1. 먼저 영역을 판별한다

| 영역 | 실제 스택 | 진입 | 성격 |
|------|----------|------|------|
| `arms/` | jQuery 3 + 바닐라 JS + Bootstrap 3(lightblue4) | `arms/template.html?page={page}` · `arms/detail.html?mode=detail` | 운영 중 메인 앱 |
| `backoffice/` | **arms와 동일한 jQuery MPA** | `backoffice/template.html?page={feature}` | 관리자 백오피스 |
| `reference/` | 정적 번들 라이브러리(npm 아님) | `<script src="../reference/...">` | 읽기 전용 자산 |

- `backoffice/package.json` 에 React 17 · Redux Toolkit · Vite 가 **선언만** 되어 있다.
  `src/` 도 `.jsx` 도 없고 `backoffice/README.md` 가 "React 는 선행 과제"라고 못박는다.
  **backoffice 신규 화면도 jQuery 로 작성한다.** JSX 를 만들면 빌드조차 되지 않는다.
- 루트 `package.json` 의 Vue 는 2026-06-23 제거됐다. 현재 루트는 arms Grunt 빌드 전용이다.
- `.ts` / `.tsx` 를 추가하지 않는다.
- `backoffice/template.html` 도 `../arms/js/common.js` 를 그대로 로드한다.
  즉 **공통 허브는 두 영역이 공유**한다. arms 쪽 `common.js` 수정은 백오피스까지 영향이 간다.

---

## 2. 페이지 라이프사이클 (이 저장소의 핵심 계약)

`arms/js/common.js` 가 전 과정을 주관한다. 페이지 스크립트는 이 흐름에 **끼어드는 쪽**이다.

```
template.html?page=reqAdd
  └ $(function(){ ... })                     common.js:26
      ├ URL 에 "landing_" 포함  → 인증 건너뜀 → runScript()
      └ 그 외                   → authUserCheck()  (GET /auth-user/me)
                                    └ $.authorization(userID, page) → runScript()
  └ runScript()                              common.js:38
      ├ topbarConfig() / supportBubble() / rightBottomTopForwardIcon()
      ├ ajax_setup()                         전역 401·403·500 핸들러 등록
      ├ includeLayout(page)                  [data-include] 스캔 → 조각 $.load()
      │     content-header    → html/{page}/content-header.html
      │     content-container → html/{page}/content-container.html
      │     page-navigation / page-sidebar / content-footer → html/template/* (landing·detail 변형)
      ├ loadTheme()
      └ $.getScript("js/{page}.js")
            ├ execDocReady()      ← 페이지가 반드시 정의해야 하는 진입점
            ├ dwr_login(...)      (landing_* 제외)
            └ menu_setting()      ROLE_USER / ROLE_MANAGER / ROLE_ADMIN 메뉴 분기
```

### 페이지가 반드시 정의해야 하는 전역 함수

| 함수 | 언제 필요한가 | 빠뜨리면 |
|------|--------------|---------|
| `execDocReady()` | **항상** | 페이지가 아무것도 안 함 (조용한 실패) |
| `dataTableClick(tempDataTable, selectedData)` | `dataTable_build` / `dataTable_extendBuild` 사용 시 | `ReferenceError` 로 테이블 렌더 중단 |
| `dataTableCallBack(settings, json)` | 〃 | 〃 |
| `dataTableDrawCallback(tableInfo)` | 〃 | 〃 |
| `jsTreeClick(selectedNode)` | `jsTreeBuild` 사용 시 | 트리 노드 클릭이 무반응 |

DataTable 콜백 3종은 `common.js` 가 `$.isFunction(dataTableDrawCallback)` 로 가드하지만,
**선언 자체가 없으면 인자 평가 시점에 ReferenceError** 가 난다. 본문이 비어 있어도 선언한다.
(`arms/js/detail_kpi.js:604-614` 가 최소 예시)

### execDocReady() 의 표준 골격

플러그인은 `<script>` 로 박지 않고 `loadPluginGroupsParallelAndSequential()` 로 올린다.
인자는 **배열의 배열** — 바깥은 병렬, 안쪽은 순차(의존 순서가 있는 묶음)다.

```javascript
function execDocReady() {
	var pluginGroups = [
		["../reference/lightblue4/docs/lib/widgster/widgster.js"],
		[
			"../reference/jquery-plugins/select2-4.0.2/dist/css/select2_lightblue4.css",
			"../reference/jquery-plugins/select2-4.0.2/dist/js/select2.min.js"
		],
		["../reference/jquery-plugins/echarts-5.5.0/dist/echarts.min.js"]
	];

	loadPluginGroupsParallelAndSequential(pluginGroups)
		.then(function () {
			$(".spinner").empty();      // 로딩 메시지 잔류 방지 (§6 참조)
			$(".widget").widgster();    // lightblue4 위젯 컨트롤 활성화
			setSideMenu("sidebar_menu_requirement", "sidebar_menu_requirement_add");
			// 이 아래부터 화면 초기화
		})
		.catch(function (error) {
			console.error("[ {page} ] 플러그인 로드 실패");
			console.error(error);
		});
}
```

전체 템플릿은 `assets/page-template/` 의 `page.js` · `content-container.html` ·
`content-header.html` 을 복사해서 시작한다.

---

## 3. 작업 레시피

### 기존 화면 수정
1. `arms/html/{page}/content-container.html` 과 `arms/js/{page}.js` 를 **둘 다** 읽는다.
   ID 규칙·렌더 함수 짝이 여기서 드러난다.
2. `Java-Service-Tree-Framework-Frontend-Web/docs/ai/06_page_playbooks/{page}.md` 가 있으면
   그 화면의 데이터·상태·디자인 규칙이 정본이므로 먼저 읽는다
   (현재 존재: `detail_dashboard.md`, `detail_kpi.md`).
3. 주변 코드 스타일에 맞춘다. 이 저장소는 ES5/ES6 가 섞여 있고 **일관성이 최신 문법보다 우선**이다.

### 새 화면 추가
`html/{page}/content-container.html` 과 `js/{page}.js` 를 **1:1 쌍**으로 만들어야 라우팅이 성립한다.
단계별 절차·진입 메뉴 등록까지는 `references/page-recipes.md` 를 따른다.

페이지 이름 prefix 가 인증 동작을 결정한다:
- `landing_*` — 인증 면제(랜딩/마케팅). `common.js` 가 URL 로 판별한다.
- `detail_*` — 인증 필요, 읽기 전용 상세. `arms/html/detail/page-sidebar.html` 의
  `targetLink('{page}')` 로 진입 링크를 등록한다.
- 그 외(`req*`, `pdService`, `analysis*`, `report*`, `dashboard` …) — 인증 필요,
  `arms/html/template/page-sidebar.html` 에 등록.

### 서버 연동
게이트웨이 prefix·에러 처리·응답 봉투는 `references/domain-and-api.md` 가 정본이다. 핵심만:
- 전역 핸들러가 401(로그인 리다이렉트) · 403(알림) · 500(알림) 을 **이미 처리**한다.
  페이지에서 중복 처리하지 않는다.
- 권한에 맞는 prefix 를 고른다: `/auth-anon`(익명) · `/auth-user` · `/auth-manager` ·
  `/auth-sche` · `/auth-admin`.
- 호출 형태는 페이지 코드의 기존 패턴을 따른다:

```javascript
$.ajax({
	url: "/auth-user/api/arms/pdService/getVersionList?c_id=" + pdServiceId,
	type: "GET",
	contentType: "application/json;charset=UTF-8",
	dataType: "json",
	progress: true,
	statusCode: {
		200: function (data) {
			// 구형 .do API: { response: [...] }
			// 신형 엔진 API: { success: true, response: {...} }
		}
	}
});
```

---

## 4. 공통 함수를 다시 만들지 않는다

`common.js`(약 2,950줄)가 트리·테이블·인증·i18n·알림·쿠키·테마·투어를 모두 갖고 있다.
시그니처와 호출 예시는 `references/common-js-api.md` 에 정리해 두었다 — **새 유틸을 쓰기 전에 거기부터 본다.**

가장 자주 쓰는 것들:

| 기능 | 함수 |
|------|------|
| 데이터 그리드 | `dataTable_build(...)` / 서버사이드는 `dataTable_extendBuild(...)` |
| 새 테이블 래퍼 | `$("#t").table({...})` — `arms/js/common/table_new.js` (백오피스 주력) |
| 트리 | `jsTreeBuild(elementId, serviceUrl, syncUrl, scrollHeight)` |
| 알림 | `jSuccess()` / `jError()` / `jNotify()` — `alert()` 금지 |
| 버튼 로딩 | `laddaBtnSetting([".btn_save"])` |
| 사이드 메뉴 활성화 | `setSideMenu("sidebar_menu_a", "sidebar_menu_a_b")` |
| 다국어 | `setLocale(locale)` + 마크업의 `data-locale="키.경로"` |
| 쿠키 | `getCookie(name)` / `setCookie(name, value, exp, ["/arms","/backoffice"])` |
| 빈값 판정 | `isEmpty(v)` / `isExist(v)` |
| 날짜 | `dateFormat(ts)` / `dateFormatSlash(ts)` / `getToday()` / `parseDateString(s)` |
| 페이지 이동 | `goToTemplatePage(pageName)` / `targetLink(path)` |

한글 함수명과 영문 함수명이 공존한다(`로드_완료_이후_실행_함수`, `톱니바퀴_초기설정`,
`검색_이벤트_트리거`). 호출 전 이름을 정확히 확인한다.

---

## 5. 지켜야 하는 표기 규칙

전체는 `references/conventions.md`. 위반이 잦은 것만 여기 둔다.

- **Bootstrap 3 전용.** `d-flex` · `ml-2` 같은 BS4/BS5 유틸은 이 테마에 존재하지 않는다.
  `col-md-*` · `pull-right` · `hidden-xs` 를 쓴다.
- **위젯 구조:** `section.widget > header > h4` + `.widget-controls` + `div.body`.
  샘플은 `arms/html/pdService/content-container.html`.
- **id 는 스네이크 케이스(언더바):** `selected_worker`, `project_status_table`.
- **HTML 속성은 한 줄에 하나씩.** 이건 취향이 아니라 `.prettierrc` 의
  `singleAttributePerLine: true` 가 강제하는 형식이다. 편집 후
  `npx prettier --write <파일>` 로 맞추면 diff 가 깔끔해진다.
  (탭 들여쓰기 · printWidth 120 · 쌍따옴표 · `bracketSameLine: true`)
- **버튼 색상은 의미가 고정**이다 — 파랑 `edit-blue`(추가) / 녹색 `edit-green`(수정) /
  빨강 `edit-red`(삭제) / 오렌지 `edit-orange`(선택 구분). 다른 색을 새로 만들지 않는다.
- **상태 색상(전역):** Done `#34d399` · Normal `#a4c6ff` · Warning `#fbbf24` · Critical `#f87171`.
  강조 데이터 텍스트는 `color: #a4c6ff`.
- **문구는 `data-locale` 바인딩**을 쓰고 로컬 폴백 파일 `arms/locales/ko.json` · `en.json`
  **두 개를 함께** 갱신한다. `jp.json` 은 건드리지 않는다 — 0바이트 사(死)파일이고
  `setLocale()` 이 요청하는 이름은 `ja.json` 이다(§6-3).
  단, 이미 한글 문구를 하드코딩하고 있는 화면 옆에 새 요소를 넣을 때는 주변 방식을 따른다
  (backoffice 19개 화면 중 `data-locale` 사용은 1개뿐이다).
- 운영 코드에 `console.log` 를 남기지 않는다. 진단용 로그는
  `console.log("[ {page} :: {fn} ] ...")` 형식을 쓰되 작업 후 정리한다.

---

## 6. 이 저장소에서 반복적으로 사람을 무는 함정

자세한 증상·우회법은 `references/pitfalls.md`. 요약:

1. **DataTable 콜백 3종 미선언 → ReferenceError** (§2 표).
2. **플러그인 로딩 메시지 잔류** — `loadPlugin()` 이 `.spinner` 에 "OO.js 다운로드 중"을 쓰고
   지우지 않는다. `.then()` 안에서 `$(".spinner").empty()` 를 호출한다.
3. **일본어 폴백이 아예 없다** — `setLocale()` 은 Global-Config 실패 시
   `/arms/locales/{locale}.json` 을 부르고 `changeLocale()` 허용값은 `["ko","ja","en"]` 이다.
   그런데 저장소에 있는 파일은 `ko.json` · `en.json` · **`jp.json`(0바이트)** 라
   `ja` 선택 시 `ja.json` 404 → 라벨이 전부 빈 값이 된다. `jp.json` 은 어느 코드도 읽지 않는
   사(死)파일이니 여기에 키를 넣지 말 것(0바이트 파일에 키 하나만 넣으면 파싱이 성공해
   **나머지 모든 라벨이 빈 값으로 덮인다** — 더 나빠진다). 일본어가 필요하면 `ja.json` 신설 또는
   Global-Config 등록을 별도 과제로 제안한다. (도움말 JSON 폴더는 `help/*/ja/` 로 `ja` 를 쓴다.)
4. **`reference/` 경로에 버전이 박혀 있다** (`echarts-5.5.0`, `select2-4.0.2`).
   기존 화면을 고칠 때는 **그 화면이 이미 로드한 버전**을 따른다(arms 는 5.4.3 · 5.5.0 혼재).
5. **`common.js` · `template.html` · `locales/*` 는 전 페이지 공용**이다.
   고치기 전에 영향 범위를 먼저 말하고, 페이지 단위로 해결할 수 있으면 그쪽을 택한다.
6. **`$.ApiGenerator` 는 저장소 어디에도 정의가 없다.** `backoffice/js/scheduleConfig/api/scheduleConfigApi.js`
   가 이것을 호출하므로 그 모듈은 현재 런타임 에러 상태다. 이 패턴을 새로 따라하지 않는다.
7. **대형 정적 도구(drawio · three.js-r165 · drawdb)는 임베드만** 한다. 내부 파일을 편집하지 않는다.

---

## 7. 라이브러리는 `reference/` 에서 먼저 찾는다

npm 설치가 아니라 저장소에 박힌 정적 번들이다. 차트·테이블·날짜선택·셀렉트·에디터·업로드 등
흔한 기능은 대부분 이미 있다. 기능 → 라이브러리 → 정확한 로드 경로 표는
`references/libraries.md` 에 있다.

목록에 없는 라이브러리가 필요하면 **코드를 쓰기 전에 먼저 제안**한다.
CDN 링크를 새로 박지 않는다(오프라인/사내망 전제).

---

## 8. 실행해서 확인하기

```bash
cd Java-Service-Tree-Framework-Frontend-Web
npm install          # Node v20.19.0 (.node-version)
npx grunt server     # = npm run dev
```

`grunt server` 는 **포트 80** 으로 정적 서빙하고, `/auth-user` · `/auth-admin` · `/auth-anon` ·
`/oauth2` · `/login` · `/dwr` 등을 `313.co.kr:80` (Stage) 로 프록시한다(`Gruntfile.js`).
확인 URL: `http://localhost/arms/template.html?page={page}`

자동화 테스트는 없다. 검증은 **브라우저 콘솔 에러 0건 + 화면 동작 육안 확인**이 기준이다.
`docs/ai/06_test_strategy/frontend-web-test-strategy.md` 의 수동 체크리스트를 쓴다.

---

## 9. 제출 전 자가 점검

- [ ] 영역(arms / backoffice)을 맞게 판단했고 스택을 섞지 않았다
- [ ] 새 페이지면 `html/{page}/content-container.html` + `js/{page}.js` 쌍이 있다
- [ ] `execDocReady()` 를 정의했고, DataTable 쓰는 페이지는 콜백 3종을 선언했다
- [ ] 공통 기능을 `common.js` 기존 함수로 처리했다(중복 구현 없음)
- [ ] Bootstrap 3 클래스만 썼고 lightblue4 위젯 구조를 따랐다
- [ ] 버튼 4색 · 상태 4색 규칙을 지켰다
- [ ] 새 문구를 `locales/ko.json` · `en.json` 에 함께 넣었다(`jp.json` 은 건드리지 않았다)
- [ ] `reference/` 밖의 새 라이브러리를 임의로 추가하지 않았다
- [ ] 태그 균형(`div`/`section`/`table`/`tr`)과 JSON 유효성을 확인했다
- [ ] `console.log` · `alert` · 임시 파일을 남기지 않았다
- [ ] 요청 범위를 넘는 집계·기능을 임의로 붙이지 않았다(YAGNI)
- [ ] 의미 있는 변경이면 `docs/ai/11_changelog/frontend-web-changelog.md` 에 한 줄 남겼다

---

## 10. 산출 및 인계

- 사용자 대상 설명은 **한국어**로 한다.
- **commit·push 하지 않는다.** 작업 요약과 함께 커밋 메시지 초안만 제시하고 커밋은 사용자가 한다.
  이 저장소의 실제 컨벤션(YouTrack 연동):
  ```
  feat : [ARMS-1160] #comment 담당자별 진행율 및 css추가
  fix : [ARMS-1160] #comment 스크롤 상단으로 이동되는 부분 수정
  refactor : [ARMS-1195] #comment 불필요 요소 정리 2026.09.15 #close #time 1h +review SR @sevoon0909
  ```
  현재 작업 브랜치는 `dev` 다(`main`/`master` 아님).
- 확신이 없는 지점(엔드포인트 스펙, 응답 필드, 디자인 판단)은 추측으로 메우지 말고
  **가정을 명시**하거나 질문한다.

---

## 11. 참조 파일 지도

이 스킬의 상세 자료 (`references/`):

| 파일 | 언제 읽나 |
|------|----------|
| `references/common-js-api.md` | 공통 함수 시그니처·호출 예시가 필요할 때 |
| `references/page-recipes.md` | 새 화면 추가 / 기존 화면 확장 절차 |
| `references/libraries.md` | 기능에 맞는 번들 라이브러리와 로드 경로 |
| `references/conventions.md` | 마크업·네이밍·색상·i18n·도움말/투어 규칙 |
| `references/domain-and-api.md` | 게이트웨이·인증·응답 계약·도메인 용어·상태 구간 |
| `references/backoffice.md` | `backoffice/` 영역에서 작업할 때 |
| `references/pitfalls.md` | 이상 동작이 보일 때 / 착수 전 함정 확인 |

저장소 자체 문서 (`Java-Service-Tree-Framework-Frontend-Web/docs/ai/`) 도 살아 있는 정본이다.
용어는 `08_domain_glossary`, 화면별 규칙은 `06_page_playbooks/{page}.md`,
변경 이력은 `11_changelog` 에 남긴다.

> ⚠️ 단, 아래 항목은 **문서가 현재 코드와 어긋나 있음을 확인**했다. 코드를 정본으로 삼는다.
> - `03_directory_structure` §3 은 backoffice 를 React(`src/`)로 서술하지만 `src/` 는 존재하지 않는다
>   (같은 폴더의 `02_tech_stack` §3 · `12_known_issues` §1 이 맞다).
> - 여러 문서가 루트 `개발규칙.txt` 를 원본으로 인용하지만 **그 파일은 저장소에 없다.**
>   코딩 규칙의 실질 정본은 `04_coding_standards/frontend-web-coding-standards.md` 다.
> - `06_page_playbooks/guide.md` 가 링크하는 `landing_test.md` 와 `landing_test` 페이지는 삭제됐다.
> - `13_deploy_runbook` 이 언급하는 `.travis.yml` 과 루트 `file/` 디렉토리는 없다
>   (CI 는 `.github/workflows/release-drafter.yml` 하나, 문서 자산은 `docs/file/`).
