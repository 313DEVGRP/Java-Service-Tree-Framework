# 표기 · 마크업 · 스타일 규칙

정본: `docs/ai/04_coding_standards/frontend-web-coding-standards.md`
(문서들이 인용하는 루트 `개발규칙.txt` 는 현재 저장소에 없다. 위 문서가 실질 정본이다.)

---

## 1. 포맷 — Prettier 가 강제한다

`.prettierrc`:
```json
{
	"printWidth": 120,
	"useTabs": true,
	"singleAttributePerLine": true,
	"bracketSameLine": true,
	"singleQuote": false,
	"trailingComma": "none",
	"semi": true,
	"bracketSpacing": true,
	"htmlWhitespaceSensitivity": "ignore",
	"endOfLine": "auto"
}
```
- **탭 들여쓰기**, 쌍따옴표, 세미콜론 유지, 후행 콤마 없음.
- `singleAttributePerLine: true` 때문에 **HTML 속성이 한 줄에 하나씩**이고,
  `bracketSameLine: true` 때문에 닫는 `>` 가 마지막 속성 줄 끝에 붙는다.
  "속성 한 줄에 하나" 규칙은 취향이 아니라 이 설정의 결과다.
- 편집 후 정렬: `npx prettier --write arms/html/{page}/content-container.html`

```html
<button
	class="btn btn-sm edit-blue"
	id="regist_pdservice"
	type="button">
	등록
</button>
```

## 2. 네이밍

- `id` 는 **스네이크 케이스(언더바)**: `selected_worker`, `project_status_table`, `kpi_assignee_account_id`.
- 사이드 메뉴 id 는 `sidebar_menu_{대분류}` / `sidebar_menu_{대분류}_{소분류}`.
- JS 변수·함수는 카멜케이스가 기본이나, **한글 함수명이 공존**한다
  (`로드_완료_이후_실행_함수`, `톱니바퀴_초기설정`, `검색_이벤트_트리거`, `laddaBtnSetting(라따적용_클래스이름_배열)`).
  새로 만들 때는 영문 카멜케이스를 쓰되, **기존 함수를 호출할 때는 이름을 정확히 확인**한다.
- 페이지 스크립트의 전역 상수는 대문자 스네이크(`KPI_COLORS`, `TIME_REQ_PAGE_SIZE`)가 관례.
- 로그 prefix: `console.log("[ {page} :: {함수} ] :: 메시지")` — `common.js` 전체가 이 형식이다.

## 3. Bootstrap 3 + lightblue4 마크업

**Bootstrap 3 전용.** BS4/BS5 유틸(`d-flex`, `ml-2`, `text-start`, `row-cols-*`)은 존재하지 않는다.
그리드는 `row` / `col-md-*` / `col-sm-*`, 정렬은 `pull-left` · `pull-right` · `clearfix`,
숨김은 `hidden-xs` · `hide`.

위젯(= 박스) 표준 구조:
```html
<section class="widget">
	<header>
		<h4>…제목…</h4>
		<div class="widget-controls">
			<a data-widgster="expand" …>
			<a data-widgster="collapse" …>
			<a data-widgster="fullscreen" …>
		</div>
	</header>
	<div class="body">…내용…</div>
</section>
```
- `data-widgster` 값: `toleft` · `toright` · `expand` · `collapse` · `restore` · `fullscreen`.
- 로드 후 `$(".widget").widgster();` 가 호출돼야 동작한다.
- 전체 참고 샘플: `arms/html/pdService/content-container.html`

`content-header.html` 표준:
```html
<h3 class="page-title font16">
	<i class="fa fa-cubes"></i>
	Product.service
	<small>Regist</small>
	<button class="btn btn-help btn-xs" data-help="project-pdService" data-help-type="page">…</button>
	<ol class="breadcrumb pull-right hidden-xs font12">…</ol>
</h3>
```

자주 쓰는 프로젝트 유틸 클래스(`arms/css/common.css` · `override.css`):
`font10`~`font18`(글자 크기) · `gradient_middle_border` · `gradient_bottom_border` ·
`darkBack` · `widget-content` · `btn-transparent` · `btn-help`

아이콘은 Font Awesome(`fa fa-*`) 과 Glyphicon(`glyphicon glyphicon-*`) 이 혼용된다.
위젯 컨트롤은 Glyphicon, 본문은 FA 가 관례다.

## 4. 색상 — 의미가 고정돼 있다

### 버튼 (`arms/css/override.css`) — 4색 외 추가 금지
| 클래스 | 의미 | 테두리색 |
|--------|------|---------|
| `edit-blue` | 신규 추가 | `#2477ff` |
| `edit-green` | 수정/업데이트 | `#2d8515` |
| `edit-red` | 삭제 | `#db2a34` |
| `edit-orange` | 선택값 구분 | (오렌지 계열) |

### 상태 (프로젝트 전역)
| 상태 | 진척률 구간 | 색 |
|------|------------|-----|
| Done / 완료 | 100% | `#34d399` |
| Normal / 정상 | 80~99% | `#a4c6ff` |
| Warning / 주의 | 50~79% | `#fbbf24` |
| Critical / 지연 | 1~49% | `#f87171` |
| 미시작 | 0% | 회색 |

### 마감 분류 (일정 화면)
지연 `#f87171` / 임박(D-7) `#fbbf24` / 예정 `#a4c6ff` / 완료 `#34d399`

- 강조 데이터 텍스트: `style="color: #a4c6ff"`
- **진척률과 상태 표기는 항상 일치**시킨다(42% 인데 Warning 으로 찍는 식의 오류 금지).
- 차트 색은 `arms/js/common/colorPalette.js` 와 위 4색을 우선한다.

### 테마
다크가 기본이고 라이트는 `body.light-theme` 로 분기한다(`override.css` 에 47곳).
새 스타일에서 배경/글자색을 하드코딩하면 라이트 테마에서 깨지므로,
기존 위젯 클래스를 재사용하거나 `body.light-theme` 대응 규칙을 같이 넣는다.

## 5. 국제화

- 마크업: `data-locale="nav.requirement.g"` (JSON 을 평탄화한 **점 표기 키**)
- 로컬 폴백 파일: `arms/locales/ko.json` · `en.json` — **둘을 함께** 갱신한다.
  하나만 넣으면 다른 언어에서 라벨이 비어 보인다.
- `arms/locales/jp.json` 은 **0바이트이고 어느 코드도 읽지 않는다.** 건드리지 않는다.
  `setLocale()` 이 부르는 이름은 `{locale}.json` 이고 허용 로케일은 `ko`·`ja`·`en` 이라
  일본어는 `ja.json` 이 있어야 하는데 그 파일이 없다(= 일본어 폴백 부재).
- arms 는 `data-locale` 바인딩이 표준이지만, backoffice 는 19개 화면 중 1개(`auditLogging`)만
  쓰고 나머지는 한글 하드코딩이다. **주변 화면의 방식을 따른다.**
- 값에 HTML 을 넣을 수 있으나 `sanitizeHTML()` 이 허용하는 태그만 남는다:
  `span, small, strong, p, b, ul, li, br`
- 로케일 원천은 Global-Config(`/auth-anon/yml/language-config/packs/language/{locale}`),
  실패 시 로컬 JSON 폴백.
- ⚠️ 코드 허용값은 `ko` · `ja` · `en` 인데 폴백 파일은 `jp.json` 이다(→ `ja` 404).
  반면 도움말 JSON 폴더는 `arms/help/*/ja/` 로 `ja` 를 쓴다.

## 6. 도움말 · 투어

- 페이지 도움말: `data-help="{key}" data-help-type="page"` → `arms/help/full-page/{locale}/{key}.json`
- 섹션 도움말: `data-help="{key}"` (타입 생략) → `arms/help/page-section/{locale}/{key}.json`
- JSON 키: `meta{l1,l2,version,lastUpdated}` · `flow` · `help_body{title,desc}` · `video{label,path}` · `sections`
- 도움말 키 네이밍: `{대분류}-{화면}`(`project-pdService`), 섹션은 `{대분류}-{화면}-section-{n}`
- 투어 스텝은 `arms/js/common/tourGuide/tgGroup.js` 에 화면별로 모아 둔다.

## 7. JavaScript 작성 관례

- **전역 함수 기반**이다. 모듈 시스템이 없고 `$.getScript` 로 올라오므로
  `import`/`export`, `type="module"` 을 쓰지 않는다.
- ES5 와 ES6 가 섞여 있다(`var` + `function` 이 다수, 일부 `let`/`const`/템플릿 리터럴/화살표 함수).
  **주변 코드 스타일에 맞추는 것이 최신 문법보다 우선**이다.
- 이벤트는 jQuery 로 건다. 동적으로 생기는 요소에는 위임(`$(document).on("click", ".x", fn)`)을 쓴다.
- 인라인 `onclick` 은 사이드바 메뉴 등 **기존에 그렇게 돼 있는 곳**에서만 유지한다. 새 코드에서는 지양.
- `alert()` 금지 → `jSuccess` / `jError` / `jNotify`.
- 운영 코드에 `console.log` 를 남기지 않는다.
- 값 검사는 `isEmpty()` / `isExist()` 를 쓴다.
- XSS: 서버·사용자 입력을 innerHTML 로 넣기 전에 이스케이프한다
  (여러 페이지가 자체 `escapeHtml()` 을 두고 있으니 해당 페이지 것을 재사용).

## 8. 편집 후 확인

- 대량 수정 후 **태그 균형**(`div`·`section`·`table`·`tr`) 확인.
- JSON 수정 후 **유효성** 확인.
- 임시/스플라이스 파일 즉시 삭제.
- `npx prettier --write` 로 포맷 정렬.
- 브라우저 콘솔 에러 0건 확인(자동 테스트가 없으므로 이게 사실상의 테스트다).
