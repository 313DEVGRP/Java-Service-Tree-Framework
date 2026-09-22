# 화면 작업 레시피

## A. 새 화면 추가 (arms)

라우팅은 파일 존재로 성립한다. 아래 2개가 없으면 `template.html?page={page}` 가 빈 화면이 된다.

### 1) 페이지 이름 정하기
prefix 가 인증·레이아웃을 결정하므로 먼저 고른다.

| prefix | 인증 | 레이아웃 | 사이드바 등록처 |
|--------|------|----------|----------------|
| `landing_*` | 면제 | 랜딩 내비/푸터 | `arms/html/template/landing-navigation.html` |
| `detail_*` | 필요 | detail 사이드바 | `arms/html/detail/page-sidebar.html` |
| 그 외 (`req*`, `pdService`, `analysis*`, `report*`, `dashboard`, `jiraConnection` …) | 필요 | 기본 사이드바 | `arms/html/template/page-sidebar.html` |

### 2) 파일 생성 (1:1 쌍)
```
arms/html/{page}/content-container.html   (필수)
arms/html/{page}/content-header.html      (선택 — 타이틀·브레드크럼·Help 버튼)
arms/js/{page}.js                          (필수 — execDocReady() 정의)
```
`assets/page-template/` 의 3개 파일을 복사해 시작한다.

### 3) 사이드바에 진입 링크 등록
기본 사이드바는 `href` 방식, detail 사이드바는 `onclick="targetLink(...)"` 방식이다.
두 방식이 섞여 있으므로 **편집하는 파일의 기존 형태를 그대로 따른다.**

```html
<!-- arms/html/template/page-sidebar.html -->
<li id="sidebar_menu_requirement_gantt">
	<a
		href="/arms/template.html?page=reqGantt"
		data-locale="nav.requirement.g">
		간트 차트<span class="font12"> - Gantt</span>
	</a>
</li>
```
```html
<!-- arms/html/detail/page-sidebar.html -->
<li id="sidebar_menu_dashboard_kpi">
	<a
		href="#"
		onclick="targetLink('detail_kpi')">
		KPI Dashboard
	</a>
</li>
```
id 는 `sidebar_menu_{대분류}` / `sidebar_menu_{대분류}_{소분류}` 규칙이다.
페이지 스크립트에서 `setSideMenu("sidebar_menu_대분류", "sidebar_menu_대분류_소분류")` 로
같은 id 를 활성화한다.

### 4) 다국어 키 추가
새 라벨은 `arms/locales/ko.json` · `en.json` **두 개**에 같은 경로로 넣고,
마크업에 `data-locale="nav.requirement.g"` 처럼 점 표기 키를 건다.
`jp.json` 은 0바이트 사(死)파일이라 건드리지 않는다(`references/pitfalls.md` §2).

### 5) 도움말(선택)
`content-header.html` 의 Help 버튼과 JSON 을 함께 만든다.
```html
<button
	class="btn btn-help btn-xs"
	data-help="project-pdService"
	data-help-type="page">
	Help
	<i class="fa fa-question"></i>
</button>
```
→ `arms/help/full-page/{ko,en,ja}/project-pdService.json`
섹션 도움말은 `data-help-type` 없이 `data-help="project-product-section-1"` →
`arms/help/page-section/{locale}/...json`.
(도움말 폴더는 `ja`, 로케일 파일은 `jp.json` — 폴더명 규칙이 다르니 주의)

### 6) 페이지 플레이북 등록(반복 작업 화면이면)
`docs/ai/06_page_playbooks/{page}.md` 를 추가하고 같은 폴더 `guide.md` 목록표에 한 줄 넣는다.

### 7) 변경 이력
`docs/ai/11_changelog/frontend-web-changelog.md` 최신 위쪽에
`- (arms) {page} 신규 추가 — ...` 형식으로 한 줄.

---

## B. 기존 화면에 위젯 하나 추가하기

1. `content-container.html` 에서 들어갈 행(`.row`)과 컬럼 폭을 정한다 (Bootstrap 3 `col-md-*`).
2. 위젯 골격을 기존 위젯에서 복사한다:
```html
<div class="col-md-6">
	<section class="widget">
		<header>
			<h4>
				<span
					class="font13"
					style="font-weight: bold">
					<i
						class="fa fa-bar-chart"
						style="vertical-align: middle; font-size: 14px"></i>
					위젯 제목
				</span>
			</h4>
			<div class="widget-controls">
				<a
					data-widgster="expand"
					title="Expand"
					href="#">
					<i class="glyphicon glyphicon-chevron-up"></i>
				</a>
				<a
					data-widgster="collapse"
					title="Collapse"
					href="#">
					<i class="glyphicon glyphicon-chevron-down"></i>
				</a>
				<a
					data-widgster="fullscreen"
					title="Fullscreen"
					href="#">
					<i
						class="glyphicon glyphicon-fullscreen"
						style="font-size: 11px"></i>
				</a>
			</div>
		</header>
		<div
			class="body"
			id="my_widget_body">
			<div
				id="my_chart"
				style="width: 100%; height: 320px"></div>
		</div>
	</section>
</div>
```
3. `js/{page}.js` 에 렌더 함수를 추가하고 `execDocReady()` 의 `.then()` 에서 호출한다.
4. 새 플러그인이 필요하면 `pluginGroups` 에 **그룹을 추가**한다(기존 그룹 순서를 흔들지 않는다).
5. 위젯 컨트롤이 동작하려면 로드 후 `$(".widget").widgster();` 가 호출돼 있어야 한다.

---

## C. DataTable 붙이기

```javascript
function renderTable(rows) {
	var columnList = [
		{ data: "c_id", title: "ID", defaultContent: "-" },
		{ data: "c_title", title: "제목", defaultContent: "-" },
		{
			data: "progressRate",
			title: "진척률",
			defaultContent: "0",
			render: function (v) {
				return statusBadge(v);   // 상태 색상은 전역 정의를 따른다
			}
		}
	];

	myTable = dataTable_build(
		"#my_table",                                   // jquerySelector
		"/auth-user/api/arms/reqAdd/T_X/getMonitor.do", // ajaxUrl
		"",                                            // jsonRoot (루트 배열이면 "")
		columnList,
		[],                                            // rowsGroupList
		[],                                            // columnDefList
		{},                                            // selectList
		[[0, "asc"]],                                  // orderList
		[],                                            // buttonList
		false                                          // isServerSide
	);
}

// ↓ 3개는 비어 있어도 반드시 선언 (미선언 시 ReferenceError)
function dataTableClick(tempDataTable, selectedData) {}
function dataTableCallBack(settings, json) {}
function dataTableDrawCallback(tableInfo) {}
```

플러그인 그룹에 DataTables 를 올려야 한다 (`references/libraries.md` §테이블 참고).
`<table id="my_table" class="table table-striped"><thead></thead><tbody></tbody></table>` 처럼
**`thead` 를 비워 두면** DataTables 가 `columnList` 의 `title` 로 헤더를 만든다.
헤더를 손으로 쓰면 컬럼 수가 어긋나 라벨이 밀린다(실제 발생했던 버그).

로컬 배열로 그릴 때는 `isAjax=false` + `data` 인자를 쓰거나,
빌드 후 `table.clear().rows.add(rows).draw()` 로 갱신한다.

---

## D. 트리 + 목록 조합 (reqAdd · detail_total_reqadd 패턴)

```javascript
function buildTree() {
	jsTreeBuild("#req_tree", "/auth-user/api/arms/reqAdd/" + tableName, undefined, "545px");
}

function jsTreeClick(selectedNode) {
	var selectId = selectedNode.attr("id").replace("node_", "");
	var selectRel = selectedNode.attr("rel");   // drive | folder | default

	if (selectRel === "drive") {
		// 루트: 전체 목록
	} else if (selectRel === "folder") {
		// 폴더: 하위 노드 목록 (getChildNodeWithParent.do 등)
	} else {
		// 리프: 단건 상세
	}
}
```
트리 CRUD 는 `jsTreeBuild` 가 `{syncUrl}/addNode.do` 등으로 **자동 동기화**한다.
별도 저장 버튼을 만들 필요가 없다.

---

## E. 차트(ECharts) 붙이기

```javascript
var myChart = null;

function renderChart(rows) {
	var el = document.getElementById("my_chart");
	if (!el) return;

	if (myChart) {
		myChart.dispose();      // 재렌더 시 인스턴스 정리 (미정리 시 리사이즈 누수)
	}
	myChart = echarts.init(el);
	myChart.setOption({
		tooltip: { trigger: "axis" },
		color: ["#a4c6ff", "#34d399", "#fbbf24", "#f87171"],
		xAxis: { type: "category", data: rows.map(function (r) { return r.label; }) },
		yAxis: { type: "value" },
		series: [{ type: "bar", data: rows.map(function (r) { return r.value; }) }]
	});
}
```
- 인스턴스를 모아 두고(`var charts = { a: null, b: null }`) 탭 전환·레이아웃 변경 시
  `triggerChartsResize()` 또는 `chart.resize()` 를 호출한다.
- 기존 화면을 고칠 때는 **그 화면이 로드한 echarts 버전**(5.4.3 또는 5.5.0)을 그대로 쓴다.
- 자주 쓰는 형태는 `arms/js/common/chart/eCharts/` 에 프리셋이 있으니 먼저 확인한다.

---

## F. 제품 → 버전 선택 필터 (분석·대시보드 공통 패턴)

`analysisTime` · `detail_kpi` 가 쓰는 표준 조합이다. 제품은 select2, 버전은 multiple-select.

```javascript
function makePdServiceSelectBox() {
	$(".chzn-select").each(function () { $(this).select2($(this).data()); });

	$.ajax({
		url: "/auth-user/api/arms/pdServicePure/getPdServiceMonitor.do",
		type: "GET",
		contentType: "application/json;charset=UTF-8",
		dataType: "json",
		progress: true,
		statusCode: {
			200: function (data) {
				for (let k in data.response) {
					let obj = data.response[k];
					$("#selected_pdService").append(new Option(obj.c_title, obj.c_id, false, false)).trigger("change");
				}
			}
		}
	});

	$("#selected_pdService").on("select2:select", function () { bindVersionDataByPdService(); });
}

function bindVersionDataByPdService() {
	$(".multiple-select option").remove();
	$.ajax({
		url: "/auth-user/api/arms/pdService/getVersionList?c_id=" + $("#selected_pdService").val(),
		type: "GET",
		dataType: "json",
		progress: true,
		statusCode: {
			200: function (data) {
				let ids = [];
				for (let k in data.response) {
					let obj = data.response[k];
					ids.push(obj.c_id);
					$(".multiple-select").append(new Option(obj.c_title, obj.c_id, true, false));
				}
				selectedVersionId = ids.join(",");
				$(".multiple-select").multipleSelect("refresh");
				loadAndRender();
			}
		}
	});
}
```
`multipleSelect` 의 `onOpen` / `onClose` 에서 `.ms-parent` 의 `z-index` 를
9999 ↔ 1000 으로 토글하는 것도 기존 화면들의 공통 처리다(드롭다운이 위젯에 가려지는 문제).

---

## G. 목업으로 먼저 만들 때

- 위치: `arms/js/data/{name}.json` (예: `kpiMockData.json`)
- **필드명·구조를 실제 API 응답 형태로 설계**한다. 목업이 곧 데이터 계약이다.
- `versionId` 같은 식별자는 실제 `c_id` 를 그대로 쓰고 가짜 ID 를 만들지 않는다.
- 구조를 바꾸면 이를 읽는 렌더 코드와 플레이북을 같이 고친다.
- 수정 후 JSON 유효성을 반드시 확인한다.
