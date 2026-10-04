# 리팩토링 가이드북 — 자바스크립트 편

## 자바스크립트 편 — 들어가며

### 이 편의 범위

자바스크립트 편은 Frontend-Web의 `arms/` 영역, 즉 jQuery와 Bootstrap 3로 만든 화면 스크립트를 대상으로 합니다. React로 만든 `backoffice/`는 구조와 규칙이 달라서 이 편에 포함하지 않습니다.

앞의 자바 편에서 설명한 기본 원칙(테스트 먼저, 기능 변경과 섞지 않기, 작게 바꾸고 확인하기)은 자바스크립트에도 그대로 적용됩니다. 이 편에서는 같은 생각을 우리 화면 코드에 맞게 풀어 쓰고, 자바에는 없지만 화면 코드에서 자주 생기는 문제(화면 출력 보안, 비동기 순서, 전역 이름)를 함께 다룹니다.

### 우리 화면 코드의 현재 모습

`arms/js`에는 우리가 직접 작성한 스크립트가 약 150개 있습니다. 리팩토링 관점에서 눈에 띄는 숫자는 다음과 같습니다.

| 모습 | 규모 |
|---|---|
| 운영 코드에 남은 `console.log` | 984곳 |
| 같은 이름·같은 목적의 함수가 여러 파일에 따로 구현됨 (`makePdServiceSelectBox`) | 21개 파일, 21가지 구현 |
| 같은 API 주소를 여러 파일에 직접 적음 (`getPdServiceMonitor.do`) | 30개 파일 |
| 화면 이스케이프 함수를 파일마다 따로 만듦 | 18개 파일 |
| 브라우저를 멈추게 하는 동기 AJAX (`async: false`) | 20곳 |
| 상태 색상 값을 코드에 직접 적음 | 205곳 |

### 어떤 항목부터 보면 될까

| 화면 코드에서 이런 모습이 보이면 | 볼 항목 |
|---|---|
| 고치기 전에 화면이 잘 도는지 확인할 방법이 없다 | JS-00 안전망 |
| `console.log`, 주석 처리된 코드가 남아 있다 | JS-01 정리 |
| `k`, `obj`, `data` 같은 이름으로는 무엇인지 모른다 | JS-02 이름 |
| 함수 하나가 길고 같은 모양의 코드가 줄지어 있다 | JS-03 함수 분해 |
| 함수 인수가 많아 호출할 때 순서가 헷갈린다 | JS-04 함수 인수 |
| 같은 함수를 페이지마다 복사해 조금씩 고쳐 쓴다 | JS-05 중복 |
| 탭·상태 값으로 if/else if 가 길게 이어진다 | JS-06 조건 로직 |
| 색상·상태 코드 같은 값을 파일마다 직접 적는다 | JS-07 상수 |
| 파일 하나가 수천 줄이다 | JS-08 파일 책임 |
| 빈 catch, 실패해도 화면에 아무 표시가 없다 | JS-09 오류 처리 |
| 서버에서 받은 값을 HTML 문자열에 그대로 이어 붙인다 | JS-10 화면 출력 보안 |
| API 주소가 화면 코드 곳곳에 적혀 있다 | JS-11 구조 |
| `async: false`, 시간을 재는 `setTimeout`, 늦은 응답이 화면을 덮어쓴다 | JS-12 비동기 순서 |
| 페이지 전역 함수 이름이 다른 스크립트와 겹칠 수 있다 | JS-13 전역 이름 |

---

## JS-00 안전망 — 바꾸기 전 화면 동작을 기록한다

### 언제 필요한가

화면 코드를 고치기 전에는 항상 필요합니다. 우리 화면 코드에는 자동 테스트가 없어서, 고친 뒤 "예전과 똑같이 동작하는지"를 확인할 다른 수단이 있어야 합니다.

### 우리 코드의 예

예를 들어 요구사항 화면(`reqAdd.js`)을 리팩토링한다면, 제품을 고르고, 버전을 고르고, 트리에서 요구사항을 누르고, 탭을 바꾸는 동작이 모두 예전처럼 되어야 합니다. 하지만 지금은 이것을 사람이 기억에 의존해 눌러 보는 것 말고는 확인할 방법이 없습니다.

### 이렇게 바꾼다

고치기 전에 그 화면의 **확인 목록**을 먼저 적어 둡니다. 목록은 작업 설명이나 커밋 메시지에 남깁니다.

```
[reqAdd 화면 확인 목록]
1. 화면을 열었을 때 브라우저 콘솔에 오류가 없다
2. 제품을 고르면 버전 목록과 요구사항 트리가 채워진다
3. 트리에서 요구사항을 누르면 상세 탭이 열린다
4. 탭(통계·편집·지라·리포트·문서·이력·삭제)을 바꾸면 각 탭의 버튼만 보인다
5. 개발자 도구 Network 탭의 요청 수와 응답 상태가 고치기 전과 같다
```

고치기 전에 이 목록대로 한 번 눌러 보고, 고친 뒤 똑같이 다시 눌러 봅니다.

### 가이드 방향

목록에는 "눈에 보이는 결과"와 함께 **콘솔 오류**와 **네트워크 요청**을 꼭 넣습니다. 화면은 멀쩡해 보여도 요청이 하나 빠지거나 두 번 나가는 문제는 이 두 가지로만 드러납니다.

같은 화면을 여러 번 고치게 되면 이 목록이 쌓여 그 화면의 점검표가 됩니다. 나중에 자동 화면 테스트를 도입할 때도 이 목록이 그대로 시나리오가 됩니다.

---

## JS-01 정리 — 디버깅 흔적과 꺼진 코드를 걷어낸다

### 언제 필요한가

개발하면서 넣은 `console.log`, 주석으로 꺼 둔 코드가 운영 코드에 남아 있을 때입니다. `console.log`는 운영 화면에서 내부 값을 노출하고, 꺼진 코드는 읽는 사람이 "이걸 다시 켜야 하나"를 고민하게 만듭니다. 팀 코딩 규칙에서도 운영 코드의 `console.log`는 금지입니다.

### 우리 코드의 예

`reqAdd.js`의 탭 이벤트에는 개발할 때 쓰던 로그와 작업 메모가 그대로 남아 있습니다. 이 파일에만 `console.log`가 73곳이고, 화면 코드 전체로는 984곳입니다.

```javascript
} else if (target === "#jira") {
    ...
    console.log("jira tab click event");
    //1-1. 제품(서비스) 아이디를 기준으로, -- $('#selected_pdService').val()
    console.log("selected_pdService::::" + $("#selected_pdService").val()); // service id
    console.log("selectedJsTreeId::::" + selectedJsTreeId); //  jsTree ID
    //1-2. 요구사항 jsTree ID 가져와서 -- selectedJsTreeId
    //2. 요구사항 테이블 ( REQADD ) 을 검색하여
    //3. JIRA_VER 정보에 체크해 주기.
    var tableName = "T_ARMS_REQADD_" + $("#selected_pdService").val();
    console.log("jira tableName" + tableName);
```

`analysisTime.js`에도 이전 계산식이 주석으로 남아 있습니다.

```javascript
//const overlap = 4;
//const height = series.length * 30;
//const height = Math.max(minHeight, Math.min(maxHeight, series.length * 16));
const width = Math.max(parseInt($("#updateRidgeLine").width()) - 15, 655);
```

### 이렇게 바꾼다

디버깅용 `console.log`와 주석 처리된 코드를 지웁니다. 아무 동작도 하지 않는 계산(`var tableName = ...`처럼 로그에만 쓰이고 버려지는 값)도 함께 지웁니다.

```javascript
} else if (target === "#jira") {
    ...
}
```

### 가이드 방향

`console.log`는 디버깅이 끝나면 커밋 전에 지웁니다. 운영에서도 꼭 남겨야 하는 기록이라면 공통 알림이나 서버 로그로 보냅니다.

작업 메모(`//1-1. … //2. …`)는 코드가 아니라 이슈나 커밋 메시지에 남깁니다. 주석 처리된 코드는 지웁니다. git 이력에 남아 있으니 필요하면 되살릴 수 있습니다.

---

## JS-02 이름 — 이름만 봐도 무엇인지 알게 한다

### 언제 필요한가

`k`, `obj`, `data`, `item`처럼 무엇이든 될 수 있는 이름을 쓸 때입니다. 화면 코드는 서버 응답을 여러 단계 가공하는 경우가 많아서, 이름이 막연하면 지금 다루는 것이 제품인지 버전인지 요구사항인지 매번 거슬러 올라가 확인해야 합니다.

### 우리 코드의 예

제품 선택 상자를 채우는 코드(`detail_kpi.js`의 `makePdServiceSelectBox`)는 서버에서 받은 제품 목록을 `k`와 `obj`로 다룹니다.

```javascript
200: function (data) {
    for (let k in data.response) {
        let obj = data.response[k];
        ...
```

### 이렇게 바꾼다

다루는 대상의 이름을 붙입니다. 배열은 `for...in`(키를 순회)보다 `forEach`나 `$.each`로 값을 바로 받는 편이 의도가 분명합니다.

```javascript
200: function (data) {
    $.each(data.response, function (i, pdService) {
        ...
```

### 가이드 방향

변수 이름에는 그 값이 무엇인지(`pdService`, `versionList`, `reqIssue`)를 씁니다. `data`, `obj`, `item`, `temp`는 범위가 아주 짧을 때만 씁니다.

같은 개념에는 같은 단어를 씁니다. 제품을 어떤 곳에서는 `pdService`, 어떤 곳에서는 `product`, 또 어떤 곳에서는 `service`라고 쓰면 읽는 사람은 셋이 다른 것이라고 생각합니다.

HTML `id`는 팀 규칙대로 언더바를 쓰는 스네이크 케이스(`selected_pdService`)를 지킵니다. 함수 이름은 같은 파일 안에서 한 가지 방식으로 통일합니다.

---

## JS-03 함수 분해 — 같은 모양이 줄지어 있으면 묶는다

### 언제 필요한가

함수 하나가 길고, 그 안에 거의 같은 모양의 코드가 여러 번 이어질 때입니다. 화면 코드에서는 특히 표의 열 정의, 차트 옵션, 버튼 상태 처리에서 자주 생깁니다.

### 우리 코드의 예

`reqStatus.js`의 `getReqIssuesCreatedTogether()`는 247줄입니다. 대부분이 표의 열 정의인데, 열마다 "값이 없으면 N/A, 있으면 파란 글씨"라는 같은 그리기 함수를 10번 반복해서 적었습니다.

```javascript
{
    name: "summary",
    title: "ALM Issue Title ",
    data: "summary",
    render: function (data, type, row, meta) {
        if (isEmpty(data) || data === "unknown") {
            return "<div style='color: #808080'>N/A</div>";
        } else {
            return "<div style='white-space: nowrap; color: #a4c6ff'>" + data + "</div>";
        }
        return data;
    },
    className: "dt-body-left",
    visible: true
},
{
    name: "key",
    ...
    render: function (data, type, row, meta) {
        if (isEmpty(data) || data === "unknown") {
            return "<div style='color: #808080'>N/A</div>";
        } else {
        ...
```

### 이렇게 바꾼다

반복되는 그리기 함수를 이름 있는 함수 하나로 빼고, 열 정의는 그 함수를 가리키기만 합니다.

```javascript
// 값이 없으면 N/A, 있으면 강조 색으로 (화면 출력 보안은 JS-10)
function renderTextOrNA(data) {
    if (isEmpty(data) || data === "unknown") {
        return "<div style='color: #808080'>N/A</div>";
    }
    return "<div style='white-space: nowrap; color: #a4c6ff'>" + escapeHtml(data) + "</div>";
}

var columnList = [
    { name: "summary", title: "ALM Issue Title", data: "summary", render: renderTextOrNA, className: "dt-body-left" },
    { name: "key",     title: "ALM Issue Key",   data: "key",     render: renderTextOrNA, className: "dt-body-left" },
    ...
];
```

열 정의가 한 줄씩 줄어서 표에 어떤 열이 있는지 한눈에 보이고, "N/A 표시 방식"을 바꿀 때는 `renderTextOrNA` 하나만 고치면 됩니다.

### 가이드 방향

함수를 나눌지 판단하는 기준은 줄 수가 아니라 "그 덩어리가 하는 일을 이름 하나로 말할 수 있는가"입니다. 같은 모양이 세 번 이상 이어지면 그 모양에 이름을 붙여 함수로 뺍니다.

표 열 정의나 차트 옵션처럼 설정이 긴 함수는 "설정을 만드는 함수"와 "화면에 그리는 함수"로 나누면 각각 읽기 쉬워집니다.

`return` 뒤에 다시 `return data;`처럼 절대 실행되지 않는 줄은 지웁니다.

---

## JS-04 함수 인수 — 인수가 많으면 객체 하나로 받는다

### 언제 필요한가

함수 인수가 많아서 호출하는 쪽에서 순서를 헷갈리기 쉬울 때입니다. 자바스크립트는 인수 타입을 검사하지 않기 때문에, 순서를 바꿔 넣어도 오류 없이 엉뚱한 값으로 동작합니다.

### 우리 코드의 예

주간 보고서 API 함수(`reportWeekly/reportWeeklyApi.js`)는 인수 8개를 순서대로 받습니다.

```javascript
var fetchWeeklyKpiReport = function (pdServiceId, pdServiceVersionLinks, selectedWeek,
                                     startDate, endDate, userGroupId, displayMode, includePerformance) {
```

호출하는 쪽에서 `startDate`와 `endDate`를 바꿔 넣거나, 마지막 `true`/`false`가 무엇인지 헷갈려도 아무도 알려 주지 않습니다.

### 이렇게 바꾼다

이름 있는 속성을 가진 객체 하나로 받습니다. 호출하는 쪽에서 각 값이 무엇인지 이름으로 드러나고, 순서를 신경 쓸 필요가 없습니다.

```javascript
var fetchWeeklyKpiReport = function (params) {
    // params: { pdServiceId, pdServiceVersionLinks, selectedWeek, startDate, endDate,
    //           userGroupId, displayMode, includePerformance }
    ...
};

ReportWeeklyApi.fetchWeeklyKpiReport({
    pdServiceId: pdServiceId,
    selectedWeek: week,
    startDate: from,
    endDate: to,
    includePerformance: true
});
```

### 가이드 방향

인수가 네 개를 넘거나 같은 종류의 값(날짜 두 개, 숫자 두 개)이 나란히 있다면 객체 하나로 받습니다.

`true`/`false` 인수로 함수 안에서 동작을 고른다면, 이름이 다른 함수 두 개로 나누는 것도 고려합니다. `fetchReport(true)`보다 `fetchReportWithPerformance()`가 읽기 쉽습니다.

---

## JS-05 중복 — 페이지마다 복사한 함수를 하나로 모은다

### 언제 필요한가

같은 목적의 함수를 페이지를 만들 때마다 복사해 와서 조금씩 고쳐 쓸 때입니다. 처음에는 같았던 코드가 페이지마다 따로 고쳐지면서 결국 모두 조금씩 달라지고, 공통 버그를 고치려면 모든 페이지를 찾아다녀야 합니다.

### 우리 코드의 예

제품 선택 상자를 만드는 `makePdServiceSelectBox()`는 21개 파일에 있고, **21개가 모두 조금씩 다릅니다.** 길이도 26줄에서 87줄까지 제각각입니다. 시작 부분은 거의 같습니다.

```javascript
// detail_kpi.js 와 dashboard.js 의 시작 부분 — 거의 같다
function makePdServiceSelectBox() {
    $(".chzn-select").each(function () {
        $(this).select2($(this).data());
    });
    $.ajax({
        url: "/auth-user/api/arms/pdServicePure/getPdServiceMonitor.do",
        type: "GET",
        ...
```

`makeVersionMultiSelectBox()`(20개 파일), 날짜 형식을 바꾸는 `formatDate()`(14개 파일)도 같은 상황입니다.

### 이렇게 바꾼다

모든 페이지에 공통인 부분(목록 불러오기, select2 초기화, 옵션 채우기)을 공통 함수 하나로 만들고, 페이지마다 달랐던 부분(선택했을 때 할 일)만 인수로 넘깁니다.

```javascript
// common 쪽에 한 번
function buildPdServiceSelect(selector, onSelect) {
    $(selector).select2();
    return $.getJSON(API.PD_SERVICE_LIST).done(function (res) {
        $.each(res.response, function (i, pdService) {
            $(selector).append($("<option>", { value: pdService.c_id, text: pdService.c_title }));
        });
        $(selector).on("change", function () { onSelect($(this).val()); });
    });
}

// 각 페이지는 자기에게 필요한 것만
buildPdServiceSelect("#selected_pdService", function (pdServiceId) {
    loadVersions(pdServiceId);
});
```

### 가이드 방향

새 페이지를 만들 때 다른 페이지에서 함수를 통째로 복사해 오지 않습니다. 먼저 `common.js`나 공통 모듈에 같은 기능이 있는지 확인하고, 없다면 그 기회에 공통 함수로 만듭니다.

이미 여러 벌로 갈라진 함수는 한 번에 합치기 어렵습니다. 화면 하나를 고칠 일이 생길 때마다 그 화면의 복사본을 공통 함수로 바꿔 나갑니다. 이때 그 페이지에만 있던 차이가 무엇인지 먼저 확인하고, 그 차이는 인수로 남깁니다.

---

## JS-06 조건 로직 — 값에 따라 갈라지는 분기는 표로 바꾼다

### 언제 필요한가

탭 이름, 상태 값처럼 정해진 값에 따라 `if / else if`가 길게 이어지고, 각 분기가 거의 같은 일을 조금씩 다르게 할 때입니다.

### 우리 코드의 예

`reqAdd.js`의 탭 이벤트는 탭 7개를 `if / else if`로 나누고, 분기마다 버튼 그룹 네 개를 보이거나 숨기는 코드를 반복합니다. 어떤 탭에서 어떤 버튼이 보이는지 알려면 28줄을 모두 읽어야 합니다.

```javascript
if (target === "#stats") {
    $(".edit_btn_group").addClass("hidden");
    $(".delete_btn_group").addClass("hidden");
    $(".jira_btn_group").addClass("hidden");
    $(".newReqDiv").hide();
} else if (target === "#edit") {
    $(".edit_btn_group").removeClass("hidden");
    $(".delete_btn_group").addClass("hidden");
    $(".jira_btn_group").addClass("hidden");
    $(".newReqDiv").hide();
} else if (target === "#jira") {
    ...
```

### 이렇게 바꾼다

"어떤 탭에서 무엇을 보여 주는가"를 표(객체) 하나로 적고, 실제로 보이고 숨기는 코드는 한 번만 씁니다.

```javascript
// 탭마다 보여 줄 버튼 그룹
var TAB_BUTTONS = {
    "#stats":   [],
    "#edit":    [".edit_btn_group"],
    "#jira":    [".jira_btn_group"],
    "#report":  [".newReqDiv"],
    "#doc":     [],
    "#history": [],
    "#delete":  [".delete_btn_group"]
};
var ALL_TAB_BUTTONS = [".edit_btn_group", ".delete_btn_group", ".jira_btn_group", ".newReqDiv"];

$('a[data-toggle="tab"]').on("shown.bs.tab", function (e) {
    var visible = TAB_BUTTONS[$(e.target).attr("href")] || [];
    $.each(ALL_TAB_BUTTONS, function (i, selector) {
        $(selector).toggle(visible.indexOf(selector) >= 0);
    });
});
```

이제 탭과 버튼의 관계가 표 하나에 모여 있어서, 새 탭을 추가할 때 표에 한 줄만 넣으면 됩니다.

단, 표로 옮기다 보면 원래 코드의 작은 차이가 드러납니다. 원래 코드에서 리포트 탭(`#report`)만 지라 버튼 그룹을 건드리지 않고 그대로 둡니다. 위 표대로 바꾸면 리포트 탭에서 지라 버튼이 숨겨지므로 동작이 달라집니다. 이런 차이를 발견하면 의도한 것인지 먼저 확인하고, 의도한 것이라면 표에 그 예외를 그대로 옮겨 동작을 똑같이 유지합니다. 차이를 고치는 일은 리팩토링이 끝난 뒤 별도 수정으로 합니다.

### 가이드 방향

정해진 값에 따라 갈라지는 분기는 객체(표)로 바꿀 수 있는지 먼저 봅니다. 분기마다 하는 일이 "값만 다르고 모양은 같다"면 표로 바꾸는 것이 거의 항상 낫습니다.

분기마다 하는 일 자체가 다르다면, 값마다 함수를 연결한 표(`{ "#jira": loadJiraTab, "#doc": loadDocTab }`)를 만들어 호출합니다.

예외적인 경우(선택된 항목이 없음 등)는 함수 앞부분에서 먼저 확인하고 빠져나갑니다. 두 경우가 모두 정상적인 흐름이라면 if/else로 나란히 두어도 됩니다.

---

## JS-07 상수 — 의미 있는 값은 한곳에 이름을 붙여 둔다

### 언제 필요한가

색상 코드, 상태 이름, 기간 같은 값을 파일마다 직접 적을 때입니다. 디자인이 바뀌어 색 하나를 바꾸려면 모든 파일을 찾아야 하고, 한 곳만 빠뜨려도 화면마다 색이 달라집니다.

### 우리 코드의 예

프로젝트 전역 상태 색상(완료 `#34d399`, 정상 `#a4c6ff`, 주의 `#fbbf24`, 위험 `#f87171`)이 코드에 205번 직접 적혀 있습니다. `detail_kpi.js`는 같은 파일 안에서도 색을 두 번 정의합니다.

```javascript
var KPI_COLORS = {
    critical: "#f87171",
    warning: "#fbbf24",
    normal: "#a4c6ff",
    done: "#34d399"
};

var PROJECT_STATUS_MAP = {
    Critical: { cls: "critical", color: "#f87171" },    // 위와 같은 값을 다시 적는다
    Warning: { cls: "warning", color: "#fbbf24" },
    Normal: { cls: "normal", color: "#a4c6ff" },
    ...
```

### 이렇게 바꾼다

공통 색상 파일(`common/colorPalette.js`)에 상태 색을 한 번 정의하고, 바뀌지 않도록 얼립니다. 각 페이지는 그것을 가져다 씁니다.

```javascript
// common/colorPalette.js
ColorPalette.status = Object.freeze({
    done: "#34d399",
    normal: "#a4c6ff",
    warning: "#fbbf24",
    critical: "#f87171"
});

// detail_kpi.js
var PROJECT_STATUS_MAP = {
    Critical: { cls: "critical", color: ColorPalette.status.critical },
    Warning:  { cls: "warning",  color: ColorPalette.status.warning },
    ...
```

### 가이드 방향

자바스크립트에는 enum이 없으므로, 정해진 값의 목록은 `Object.freeze()`로 얼린 객체로 만들어 한곳에 둡니다. 얼려 두면 실수로 값을 바꾸는 코드가 있어도 원래 값이 지켜집니다.

색상처럼 여러 화면이 공유하는 값은 공통 파일에, 한 화면에서만 쓰는 값은 그 파일 맨 위에 둡니다. 코드 중간에 `"#f87171"`이나 `"Critical"` 같은 값이 직접 나오지 않게 합니다.

---

## JS-08 파일 책임 — 수천 줄짜리 화면 스크립트를 기능별로 나눈다

### 언제 필요한가

화면 스크립트 하나가 수천 줄이 되어, 한 기능을 고치려고 해도 파일 전체를 오가야 할 때입니다. 이런 파일은 여러 사람이 동시에 고치기 어렵고, 고칠 때마다 충돌이 납니다.

### 우리 코드의 예

`reqGantt.js`는 3,628줄에 함수가 97개입니다. 파일 안에서 작성자가 이미 구역을 나눠 두었습니다.

```
reqGantt.js (3,628줄)
 ├ 간트 차트 그리기
 ├ // --- Root, Drive, Folder 데이터 테이블 설정 ---
 ├ // ------------------ 편집하기 ------------------
 └ // --- select2 (사용자 자동완성 검색) 설정 ---
```

`ai-agent-init.js`(3,502줄), `common.js`(2,951줄), `reqStatus.js`(2,876줄)도 비슷한 크기입니다.

### 이렇게 바꾼다

이미 주석으로 나눠 둔 구역을 따라 파일을 나눕니다. 우리 저장소에는 화면별 하위 폴더에 기능 파일을 두는 방식이 이미 있습니다(`adms/` 아래 `wiki-lock.js`, `wiki-list.js` 등).

```
reqGantt.js              ← 진입점(execDocReady)과 화면 초기화만
reqGantt/gantt-chart.js  ← 간트 차트
reqGantt/folder-table.js ← Root·Drive·Folder 데이터 테이블
reqGantt/edit.js         ← 편집
reqGantt/user-search.js  ← 사용자 자동완성
```

진입 파일은 `loadPluginGroupsParallelAndSequential`로 하위 파일들을 불러온 뒤 초기화합니다.

### 가이드 방향

화면 스크립트의 진입 파일에는 진입점(`execDocReady`)과 화면 초기화 흐름만 두고, 기능은 화면 이름의 하위 폴더 파일로 나눕니다.

파일 안에 주석으로 큰 구역을 나누고 싶어진다면, 그 구역이 따로 파일이 될 때가 된 것입니다.

`common.js`는 모든 화면이 함께 쓰므로 특히 조심해서 다룹니다. 한 화면에서만 쓰는 함수가 `common.js`에 들어가 있다면 그 화면 쪽으로 옮깁니다.

---

## JS-09 오류 처리 — 실패를 조용히 넘기지 않는다

### 언제 필요한가

`catch`로 오류를 잡고 아무것도 하지 않을 때, 또는 요청이 실패했는데 화면에는 아무 표시가 없어서 사용자가 "데이터가 없는 것"으로 오해할 때입니다.

### 우리 코드의 예

`aiChat.js`는 응답 앞부분의 요약 데이터를 해석하다 실패하면 빈 `catch`로 넘깁니다. 해석에 실패했다는 사실이 어디에도 남지 않아서, 요약이 화면에 안 나와도 원인을 알 수 없습니다.

```javascript
try {
    return {
        summaryData: JSON.parse(content.substring(8, newline)),
        text: content.substring(newline + 1)
    };
} catch(e) {}
```

### 이렇게 바꾼다

실패를 의도적으로 넘기는 경우라도, 왜 넘기는지 적고 개발 중에 알아볼 수 있는 흔적을 남깁니다. 사용자가 알아야 하는 실패라면 공통 알림으로 알립니다.

```javascript
} catch (e) {
    // 요약 줄이 없거나 형식이 다르면 본문만 보여 준다 (요약은 선택 기능)
    return { summaryData: null, text: content };
}
```

### 가이드 방향

빈 `catch`는 쓰지 않습니다. 넘겨도 되는 실패라면 그 이유를 주석으로 적고 대체 값을 돌려줍니다. 넘기면 안 되는 실패라면 `jError()`로 사용자에게 알립니다.

AJAX의 401·403·500 응답은 `common.js`의 전역 처리기가 이미 처리합니다. 화면 코드에서는 그 밖의 실패, 특히 **"데이터가 없음"과 "불러오기 실패"를 구분해서 보여 주는 것**에 신경 씁니다. 실패했는데 빈 표만 보이면 사용자는 데이터가 없다고 생각합니다.

---

## JS-10 화면 출력 보안 — 받은 값을 HTML 에 넣을 때는 이스케이프한다

### 언제 필요한가

서버에서 받은 값을 HTML 문자열에 이어 붙여 `.html()`이나 표 그리기 함수로 화면에 넣을 때입니다. 그 값 안에 `<script>`나 `<img onerror=...>` 같은 문자열이 들어 있으면 브라우저는 이를 코드로 실행합니다. 특히 Jira 이슈 제목이나 사용자 이름처럼 **바깥 사람이 입력한 값**은 반드시 이스케이프해야 합니다.

### 우리 코드의 예

앞의 JS-03에서 본 `reqStatus.js`의 표 그리기 함수는 ALM(Jira 등) 이슈 제목을 그대로 HTML에 넣습니다. 누군가 Jira 이슈 제목에 스크립트를 넣으면 이 화면을 연 모든 사람의 브라우저에서 실행됩니다.

```javascript
return "<div style='white-space: nowrap; color: #a4c6ff'>" + data + "</div>";
```

`reportPerformance.js`도 담당자 이름을 이스케이프 없이 선택 상자에 넣습니다.

```javascript
options.push('<option value="' + u.accountId + '">' + u.displayName + "</option>");
$("#user-group-multiselect").html(options.join(""));
```

한편 이스케이프 함수는 이미 있는데, 18개 파일이 각자 이름을 달리해 따로 만들어 쓰고 있습니다(`escapeHtml`, `agmEsc`, `aghEsc`, `agdEsc` …).

### 이렇게 바꾼다

값을 HTML로 넣을 필요가 없다면 jQuery가 알아서 처리하게 합니다.

```javascript
$("<option>", { value: u.accountId, text: u.displayName })    // text 로 넣으면 그대로 글자로 표시된다
```

HTML 문자열을 직접 만들어야 한다면, 모든 화면이 함께 쓰는 이스케이프 함수 하나를 `common.js`에 두고 바깥 값을 넣을 때마다 거칩니다.

```javascript
// common.js — 한 곳에만
function escapeHtml(value) {
    return $("<div>").text(value == null ? "" : value).html().replace(/"/g, "&quot;");
}

return "<div style='white-space: nowrap; color: #a4c6ff'>" + escapeHtml(data) + "</div>";
```

### 가이드 방향

서버에서 받은 값을 화면에 넣을 때는 `.text()`나 `$("<태그>", { text: 값 })`를 먼저 씁니다. HTML 문자열을 이어 붙여야 할 때는 바깥 값을 반드시 `escapeHtml()`로 감쌉니다. 속성값(`value="..."`, `title="..."`)에 넣는 값도 마찬가지입니다.

마크다운처럼 HTML로 바꿔서 보여 줘야 하는 내용은 변환한 결과를 정화 라이브러리(DOMPurify)를 거쳐 넣습니다.

이스케이프 함수는 파일마다 새로 만들지 않고 공통 함수를 씁니다. 파일마다 만들면 어떤 것은 큰따옴표를 바꾸고 어떤 것은 바꾸지 않는 식으로 품질이 갈라집니다.

---

## JS-11 구조 — API 주소와 화면 그리기를 분리한다

### 언제 필요한가

같은 API 주소가 여러 화면 코드에 직접 적혀 있을 때, 또는 한 함수 안에서 서버 호출, 데이터 가공, 화면 그리기가 모두 섞여 있을 때입니다. 주소가 바뀌면 모든 파일을 찾아야 하고, 섞인 함수는 화면 모양만 바꾸고 싶어도 호출 코드까지 함께 읽어야 합니다.

### 우리 코드의 예

제품 목록을 불러오는 주소 `/auth-user/api/arms/pdServicePure/getPdServiceMonitor.do`가 30개 파일에, 버전 목록 주소 `/auth-user/api/arms/pdService/getVersionList`가 21개 파일에 직접 적혀 있습니다.

```javascript
// adms.js, ai-agent.js, analysisTime.js, dashboard.js … 30개 파일
$.ajax({ url: "/auth-user/api/arms/pdServicePure/getPdServiceMonitor.do", ... });
```

### 이렇게 바꾼다

자주 쓰는 API 주소를 한곳에 모으고, 서버를 부르는 함수를 따로 둡니다. 우리 저장소에는 이미 `dashboard/api/dashboardApi.js`, `analysis/api/resourceApi.js`처럼 API 호출만 모은 파일이 있으므로 같은 방식을 따릅니다.

```javascript
// common/api/armsApi.js
var API = Object.freeze({
    PD_SERVICE_LIST: "/auth-user/api/arms/pdServicePure/getPdServiceMonitor.do",
    VERSION_LIST: "/auth-user/api/arms/pdService/getVersionList"
});

var ArmsApi = {
    pdServices: function () { return $.getJSON(API.PD_SERVICE_LIST); },
    versions: function (pdServiceId) { return $.getJSON(API.VERSION_LIST, { c_id: pdServiceId }); }
};

// 화면 코드는 그리기에만 집중한다
ArmsApi.versions(pdServiceId).done(function (res) {
    renderVersionOptions(res.response);
});
```

### 가이드 방향

여러 화면이 쓰는 API 주소는 공통 API 파일에 이름을 붙여 둡니다. 한 화면에서만 쓰는 주소는 그 화면 파일 맨 위에 상수로 둡니다. 코드 중간에 주소 문자열이 직접 나오지 않게 합니다.

화면 함수는 "데이터를 받아 오는 부분"과 "받은 데이터로 화면을 그리는 부분"으로 나눕니다. 그리는 함수가 데이터를 인수로 받으면, 서버 없이도 가짜 데이터로 화면을 확인할 수 있습니다.

---

## JS-12 비동기 순서 — 시간에 기대지 말고 순서를 코드로 보장한다

### 언제 필요한가

AJAX 응답이나 라이브러리 로드의 순서를 시간에 맡길 때입니다. 동기 요청(`async: false`)으로 순서를 억지로 맞추거나, `setTimeout`으로 "이 정도 기다리면 끝났겠지" 하고 다음 일을 하거나, 여러 번 보낸 요청 중 늦게 도착한 응답이 최신 화면을 덮어쓰는 경우가 여기에 해당합니다.

### 우리 코드의 예

`analysisTime.js`는 버전 목록을 동기 요청으로 불러옵니다. 이 요청이 끝날 때까지 브라우저 전체가 멈춥니다. 화면 코드 전체에 이런 요청이 20곳 있습니다.

```javascript
$.ajax({
    url: "/auth-user/api/arms/pdService/versions-with-date?c_id=" + pdserviceId,
    type: "GET",
    async: false,          // 응답이 올 때까지 브라우저가 멈춘다
    ...
```

같은 파일은 PDF 내보내기에 필요한 라이브러리를 **5초 뒤에** 불러옵니다. 사용자가 화면을 열고 5초 안에 PDF 내보내기를 누르면 라이브러리가 아직 없어서 실패합니다.

```javascript
setTimeout(function () {
    var script = document.createElement("script");
    script.src = "../reference/jquery-plugins/dataTables-1.10.16/extensions/Buttons/js/pdfmake.min.js";
    document.head.appendChild(script);
}, 5000); // 5초 후에 실행됩니다.
```

### 이렇게 바꾼다

동기 요청 대신 응답이 온 뒤에 할 일을 이어서 적습니다.

```javascript
$.getJSON(API.VERSION_LIST_WITH_DATE, { c_id: pdServiceId })
    .done(function (res) {
        renderVersionStats(res.response);   // 응답이 온 다음에 할 일
    });
```

라이브러리는 "필요한 순간"에 불러오고, 다 불러온 뒤에 실행합니다.

```javascript
function exportPdf() {
    loadPluginGroupsParallelAndSequential([[PDFMAKE_JS, VFS_FONTS_JS]])
        .then(function () { table.button(".buttons-pdf").trigger(); });
}
```

여러 번 보낼 수 있는 요청(제품을 빠르게 바꿔 고르는 경우 등)은, 응답이 도착했을 때 그것이 아직 최신 요청의 응답인지 확인하고 아니면 버립니다.

```javascript
var latestRequest = 0;
function loadPdService(pdServiceId) {
    var requestNo = ++latestRequest;
    ArmsApi.versions(pdServiceId).done(function (res) {
        if (requestNo !== latestRequest) return;   // 더 새 요청이 있으면 이 응답은 버린다
        renderVersionOptions(res.response);
    });
}
```

### 가이드 방향

`async: false`는 새로 쓰지 않습니다. 순서가 필요하면 `.done()`이나 `.then()`으로 이어 적습니다.

`setTimeout`은 "나중에 실행"이 목적일 때만 씁니다. "끝났을 것 같은 시간까지 기다리기"에 쓰지 않습니다. 끝나는 시점을 알려 주는 콜백이나 Promise가 있다면 그것을 씁니다.

사용자가 빠르게 여러 번 바꿀 수 있는 선택(제품, 버전, 작업 목록)에 연결된 요청은 늦게 도착한 응답이 최신 화면을 덮어쓰지 않도록 확인합니다. 버튼을 두 번 눌러 요청이 두 번 나가는 것도 같은 문제이므로, 요청 중에는 버튼을 비활성화합니다.

---

## JS-13 전역 이름 — 페이지 함수는 겹치지 않는 이름이나 묶음 안에 둔다

### 언제 필요한가

화면 스크립트의 함수가 모두 전역(`window`)에 선언될 때입니다. 한 화면에는 `common.js`, 그 화면의 진입 스크립트, 하위 기능 스크립트, 차트 같은 공통 모듈이 한 페이지 안에 함께 올라옵니다. 이들 중 두 파일에 같은 이름의 함수가 있으면 나중에 불러온 쪽이 앞의 것을 조용히 덮어쓰고, 오류 없이 엉뚱한 함수가 실행됩니다.

### 우리 코드의 예

화면 코드에 최상위 전역 함수가 2,475개 있습니다. `formatDate`는 14개 파일에, `dataTableCallBack`은 20개 파일에 같은 이름으로 선언되어 있습니다. 지금은 대부분 다른 화면에서 쓰여서 한 페이지에서 만나지 않지만, 어떤 화면이 이 중 두 파일을 함께 불러오게 되는 순간 한쪽이 다른 쪽을 덮어씁니다.

최근에 만든 AI Agent 화면들은 이 문제를 피하려고 화면마다 함수 이름에 접두어를 붙였습니다(`agmEsc`, `aghEsc`, `agdEsc`).

### 이렇게 바꾼다

새 화면의 함수는 화면 이름으로 만든 객체 하나에 담거나, 최소한 화면 접두어를 붙입니다.

```javascript
// 화면 하나 = 전역 이름 하나
var ReqGantt = {
    init: function () { ... },
    renderChart: function (data) { ... },
    formatDate: function (value) { ... }     // 다른 화면의 formatDate 와 겹치지 않는다
};

function execDocReady() {        // common.js 가 부르는 진입점만 전역으로 둔다
    ReqGantt.init();
}
```

### 가이드 방향

`common.js`가 화면마다 부르는 `execDocReady()` 같은 진입점만 전역 함수로 두고, 나머지는 화면 이름의 객체 안에 둡니다. 기존 화면을 고칠 때는 그 파일 안의 관례(접두어 방식이면 접두어)를 따릅니다.

`formatDate`처럼 여러 화면이 각자 만든 같은 이름의 도우미 함수는, 같은 동작이라면 공통 함수 하나로 합칩니다(JS-05). 동작이 달라야 한다면 이름을 다르게 해서 겹치지 않게 합니다.

`common.js`에 있는 함수와 같은 이름의 함수를 화면 파일에 새로 만들지 않습니다. 만들면 그 화면에서는 공통 함수가 사라집니다.
