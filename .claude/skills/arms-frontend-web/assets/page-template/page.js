////////////////////////////////////////////////////////////////////////////////////////
// {page} · {화면 목적 한 줄}
//  - 진입: template.html?page={page}   (detail_* 는 detail.html?mode=detail 사이드바 경유)
//  - 인증: landing_* = 면제 / 그 외 = common.js authUserCheck()
//  - 데이터: {엔드포인트 또는 목업 경로}
//  - 라이브러리: reference/ 번들만 사용 (신규 추가 없음)
////////////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////////////
// 상태/분류 색상 (프로젝트 전역 정의 · docs/ai/08_domain_glossary)
////////////////////////////////////////////////////////////////////////////////////////
var PAGE_COLORS = {
	critical: "#f87171",
	warning: "#fbbf24",
	normal: "#a4c6ff",
	done: "#34d399"
};

// 페이지 전역 상태 (모듈 시스템이 없으므로 var 전역이 관례)
var pageDataTable;
var pageCharts = {};

////////////////////////////////////////////////////////////////////////////////////////
// Document Ready — common.js 가 $.getScript 직후 호출하는 진입점. 이름을 바꾸지 않는다.
////////////////////////////////////////////////////////////////////////////////////////
function execDocReady() {
	var pluginGroups = [
		["../reference/lightblue4/docs/lib/widgster/widgster.js"],
		[
			"../reference/jquery-plugins/select2-4.0.2/dist/css/select2_lightblue4.css",
			"../reference/jquery-plugins/select2-4.0.2/dist/js/select2.min.js"
		],
		[
			"../reference/jquery-plugins/dataTables-1.10.16/media/css/jquery.dataTables_lightblue4.css",
			"../reference/jquery-plugins/dataTables-1.10.16/extensions/Responsive/css/responsive.dataTables_lightblue4.css",
			"../reference/jquery-plugins/dataTables-1.10.16/media/js/jquery.dataTables.min.js",
			"../reference/jquery-plugins/dataTables-1.10.16/extensions/Responsive/js/dataTables.responsive.min.js"
		]
		// 차트가 필요하면: ["../reference/jquery-plugins/echarts-5.5.0/dist/echarts.min.js"]
	];

	loadPluginGroupsParallelAndSequential(pluginGroups)
		.then(function () {
			console.log("[ {page} ] 플러그인 로드 완료");

			// 로드 완료 후에도 남는 ".spinner" 문구 제거 (common.js loadPlugin 의 알려진 동작)
			$(".spinner").empty();

			// lightblue4 위젯 컨트롤(접기/펼치기/전체화면) 활성화
			$(".widget").widgster();

			// 사이드바 메뉴 활성화 — page-sidebar.html 의 id 와 일치시킨다
			setSideMenu("sidebar_menu_대분류", "sidebar_menu_대분류_소분류");

			initEvents();
			loadData();
		})
		.catch(function (error) {
			console.error("[ {page} ] 플러그인 로드 중 오류 발생");
			console.error(error);
		});
}

////////////////////////////////////////////////////////////////////////////////////////
// 이벤트 바인딩
////////////////////////////////////////////////////////////////////////////////////////
function initEvents() {
	// 동적으로 생성되는 요소는 위임으로 건다
	$(document).on("click", "#search_button", function () {
		loadData();
	});
}

////////////////////////////////////////////////////////////////////////////////////////
// 데이터 조회 — 401/403/500 은 common.js ajax_setup() 전역 핸들러가 처리한다
////////////////////////////////////////////////////////////////////////////////////////
function loadData() {
	$.ajax({
		url: "/auth-user/api/arms/{리소스}/{액션}.do",
		type: "GET",
		contentType: "application/json;charset=UTF-8",
		dataType: "json",
		progress: true,
		statusCode: {
			200: function (data) {
				// 구형 .do: data.response  /  신형 엔진 API: data.success && data.response
				render(data.response || []);
			}
		},
		error: function (e) {
			jError("데이터 조회 중 에러가 발생했습니다.");
		}
	});
}

////////////////////////////////////////////////////////////////////////////////////////
// 렌더
////////////////////////////////////////////////////////////////////////////////////////
function render(rows) {
	var columnList = [
		{ data: "c_id", title: "ID", defaultContent: "-" },
		{ data: "c_title", title: "제목", defaultContent: "-" }
	];

	pageDataTable = dataTable_build(
		"#page_table", // jquerySelector
		"", // ajaxUrl (로컬 데이터면 빈 값 + isAjax=false)
		"", // jsonRoot
		columnList,
		[], // rowsGroupList
		[], // columnDefList
		{}, // selectList
		[[0, "asc"]], // orderList
		[], // buttonList
		false, // isServerSide
		null, // scrollY
		rows, // data
		false // isAjax
	);
}

////////////////////////////////////////////////////////////////////////////////////////
// DataTable 전역 콜백 — common.js 가 호출한다. 비어 있어도 반드시 선언(미선언 시 ReferenceError)
////////////////////////////////////////////////////////////////////////////////////////
function dataTableClick(tempDataTable, selectedData) {}
function dataTableCallBack(settings, json) {}
function dataTableDrawCallback(tableInfo) {}
