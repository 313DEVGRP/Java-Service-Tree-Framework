# `reference/` 번들 라이브러리와 실제 로드 경로

`reference/` 는 npm 의존성이 아니라 **저장소에 직접 들어 있는 정적 파일**이다.
`loadPluginGroupsParallelAndSequential()` 의 배열에 경로 문자열로 넣어 로드한다.
아래 경로는 **현재 페이지 스크립트들이 실제로 쓰고 있는 문자열**을 모은 것이므로 그대로 복사해 쓰면 된다.

> 새 라이브러리를 CDN/npm 으로 추가하기 전에 여기서 먼저 찾는다. 없으면 **코드 작성 전에 제안**한다.
> 폴더명에 버전이 박혀 있어(`echarts-5.5.0`) 업그레이드 시 경로가 깨진다. 경로 하드코딩에 주의.

---

## 1. 거의 모든 페이지가 쓰는 기본 묶음

```javascript
["../reference/lightblue4/docs/lib/widgster/widgster.js"]          // 위젯 접기/펼치기/전체화면
["../reference/light-blue/lib/vendor/jquery.ui.widget.js"]         // 일부 플러그인 선행 의존
["../reference/lightblue4/docs/lib/slimScroll/jquery.slimscroll.min.js"]
```
`template.html` 이 이미 전역 로드하는 것(다시 올릴 필요 없음):
jQuery · jQuery UI · Bootstrap 3(sass) · jquery.cookie · **jNotify** · Ladda + spin.js ·
topbar.js · matchHeight · Messenger · TourGuide · CKEditor4 · `arms/js/common.js` · `dwrChat.js` ·
lightblue4 `app.js` · `css/override.css`(→ `common.css`, `community.css` import) · `fontawesome.css`

---

## 2. 테이블 / 그리드

```javascript
[
	"../reference/jquery-plugins/dataTables-1.10.16/media/css/jquery.dataTables_lightblue4.css",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Responsive/css/responsive.dataTables_lightblue4.css",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Select/css/select.dataTables_lightblue4.css",
	"../reference/jquery-plugins/dataTables-1.10.16/media/js/jquery.dataTables.min.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Responsive/js/dataTables.responsive.min.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Select/js/dataTables.select.min.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/RowGroup/js/dataTables.rowsGroup.min.js",
	// Export 버튼이 필요할 때만 아래 5개 추가
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Buttons/js/dataTables.buttons.min.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Buttons/js/buttons.html5.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Buttons/js/buttons.print.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Buttons/js/jszip.min.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Buttons/js/pdfmake.min.js",
	"../reference/jquery-plugins/dataTables-1.10.16/extensions/Buttons/js/vfs_fonts.js"
]
["../arms/js/common/table_new.js"]   // $.fn.table 래퍼 (백오피스 패턴)
```
`_lightblue4` 접미사가 붙은 CSS 가 테마에 맞춘 변형본이다. **원본 CSS 대신 이것을 쓴다.**

엑셀형 편집 시트:
```javascript
[
	"../reference/jquery-plugins/jspreadsheet-ce-4.13.1/dist/jsuites.css",
	"../reference/jquery-plugins/jspreadsheet-ce-4.13.1/dist/jspreadsheet.css",
	"../reference/jquery-plugins/jspreadsheet-ce-4.13.1/dist/jspreadsheet.theme.css",
	"../reference/jquery-plugins/jspreadsheet-ce-4.13.1/dist/jsuites.js",
	"../reference/jquery-plugins/jspreadsheet-ce-4.13.1/dist/index.js"
]
```

---

## 3. 트리 / 칸반 / 간트 / 캘린더

```javascript
// jstree (v.pre1.0 — common.js jsTreeBuild() 전용)
[
	"../reference/jquery-plugins/jstree-v.pre1.0/_lib/jquery.cookie.js",
	"../reference/jquery-plugins/jstree-v.pre1.0/_lib/jquery.hotkeys.js",
	"../reference/jquery-plugins/jstree-v.pre1.0/jquery.jstree.js"
]
// 칸반
["../reference/jquery-plugins/jkanban-1.3.1/dist/jkanban.min.css",
 "../reference/jquery-plugins/jkanban-1.3.1/dist/jkanban.min.js"]
// 간트 (frappe-gantt)
["../reference/jquery-plugins/gantt-0.6.1/dist/frappe-gantt.css",
 "../reference/jquery-plugins/gantt-0.6.1/dist/frappe-gantt.js"]
// 캘린더
["../reference/jquery-plugins/fullcalendar-6.1.15/dist/index.global.js",
 "../reference/jquery-plugins/fullcalendar-6.1.15/packages/core/locales-all.global.js"]
```
jstree 아이콘은 `themes/` 의 PNG(`home.png` · `ic_explorer.png` · `attibutes.png`)를 쓴다.

---

## 4. 차트 / 시각화

| 용도 | 경로 |
|------|------|
| ECharts (신규 기본) | `../reference/jquery-plugins/echarts-5.5.0/dist/echarts.min.js` |
| ECharts (기존 화면 호환) | `../reference/jquery-plugins/echarts-5.4.3/dist/echarts.min.js` |
| D3 (신규) | `../reference/jquery-plugins/d3-6.7.0/d3.min.js` |
| D3 (기존 호환) | `../reference/jquery-plugins/d3-5.16.0/d3.min.js` |
| Sankey | `../reference/jquery-plugins/d3-sankey-v0.12.3/d3-sankey.min.js` |
| GitHub 잔디 히트맵 | `./js/analysis/time/calendar_yearview_blocks_analysisTime.js` + `../reference/jquery-plugins/github-calendar-heatmap/css/calendar_yearview_blocks.css` |
| 워드 클라우드 | `../reference/jquery-plugins/jQCloud-2.0.3/dist/jqcloud.css` · `.../jqcloud.js` |
| 유체 게이지 | `../reference/jquery-plugins/javascript-fluid-meter-master/…` (`arms/js/fluid-meter.js` 참고) |
| 타임라인 차트 | `timelines-chart-2.11.8` · `jquery.timeline-2.1.3` · `TimelineJS3-3.9.3` |
| 기타 | `c3-0.7.20` · `Jit-2.0.1` · `info-chart-v1` · `dojichart-master` · `d3-ridgeline-plot` |

**한 페이지에 ECharts 버전을 두 개 올리지 않는다.** 기존 화면은 그 화면이 쓰던 버전을 유지한다.
자주 쓰는 차트 형태는 `arms/js/common/chart/eCharts/`, `arms/js/common/chart/d3/` 에 프리셋이 있다.
색상은 `arms/js/common/colorPalette.js` 와 전역 상태 4색을 따른다.

---

## 5. 폼 컨트롤

```javascript
// 단일 셀렉트 (검색·태그) — 표준
["../reference/jquery-plugins/select2-4.0.2/dist/css/select2_lightblue4.css",
 "../reference/jquery-plugins/select2-4.0.2/dist/js/select2.min.js"]
// 다중 선택 드롭다운 — 버전 다중 선택의 표준
["../reference/jquery-plugins/multiple-select-1.5.2/dist/multiple-select-bluelight.css",
 "../reference/jquery-plugins/multiple-select-1.5.2/dist/multiple-select.min.js"]
// 양쪽 이동형 다중 선택
["../reference/jquery-plugins/lou-multi-select-0.9.12/css/multiselect-lightblue4.css",
 "../reference/jquery-plugins/lou-multi-select-0.9.12/js/jquery.multi-select.js",
 "../reference/jquery-plugins/lou-multi-select-0.9.12/js/jquery.quicksearch.js"]
// 날짜 + 시간
["../reference/jquery-plugins/datetimepicker-2.5.20/build/jquery.datetimepicker.min.css",
 "../reference/jquery-plugins/datetimepicker-2.5.20/build/jquery.datetimepicker.full.min.js"]
// 날짜만 (lightblue 계열)
["../reference/light-blue/lib/bootstrap-datepicker.js"]
// 부트스트랩 셀렉트
["../reference/lightblue4/docs/lib/bootstrap-select/dist/js/bootstrap-select.min.js"]
// Cron 표현식 편집
["../reference/jquery-plugins/cron-editor-master/css/jquery-ui_arms.css",
 "../reference/jquery-plugins/cron-editor-master/js/jquery-ui.js",
 "../reference/jquery-plugins/cron-editor-master/js/jquery.croneditor_arms.js"]
```
그 밖에: `jquery-date-range-picker-0.21.1`(기간), `kevalbhatt-timezone-picker-2.0.0`(타임존),
`jquery.repeater-1.2.1`(반복 입력행), `twbs-pagination-master`(페이지네이션),
폼 검증은 lightblue4 번들의 `parsleyjs`(`../reference/lightblue4/docs/lib/parsleyjs/dist/parsley.min.js`
+ `i18n/ko.js`).

---

## 6. 파일 · 문서 · 에디터

```javascript
// 파일 업로드 (blueimp) — template.html 의 업로드 템플릿과 함께 쓴다
[
	"../reference/light-blue/lib/vendor/http_blueimp.github.io_JavaScript-Templates_js_tmpl.js",
	"../reference/light-blue/lib/vendor/http_blueimp.github.io_JavaScript-Load-Image_js_load-image.js",
	"../reference/light-blue/lib/vendor/http_blueimp.github.io_JavaScript-Canvas-to-Blob_js_canvas-to-blob.js",
	"../reference/light-blue/lib/jquery.iframe-transport.js",
	"../reference/light-blue/lib/jquery.fileupload.js",
	"../reference/light-blue/lib/jquery.fileupload-fp.js",
	"../reference/light-blue/lib/jquery.fileupload-ui.js"
]
```
| 용도 | 경로 |
|------|------|
| PDF 뷰어 | `../reference/jquery-plugins/pdfjs-3.11.174-dist/build/pdf.js` (+ `pdf.worker.js`, `web/viewer.html`) |
| diff 시각화 | `../reference/jquery-plugins/diff2html-2.12.2/dist/diff2html.min.css` · `diff2html.min.js` · `diff2html-ui.min.js` |
| 코드 강조 | `../reference/jquery-plugins/highlight.js-11.10.0/highlight.js.lib/highlight.min.js` (+ `src/styles/arta.css`, 줄번호 `highlightjs-line-numbers.js`) |
| DOM → 이미지 | `../reference/jquery-plugins/html2canvas-1.4.1/html2canvas.js` |
| PPTX 렌더 | `PPTXjs-1.21.1` |
| 리치 텍스트 | CKEditor4 (`template.html` 전역 로드). **성능 이슈로 신규 사용 지양** — `CKEDITOR.md` 참고 |

---

## 7. 애니메이션 / 랜딩

| 용도 | 경로 |
|------|------|
| 슬라이더 | `../reference/jquery-plugins/swiper-11.1.4/swiper-bundle.min.css` · `swiper-bundle.min.js` (헬퍼 `arms/js/common/swiperHelper.js`, 스타일 `arms/css/customSwiper.css`) |
| 애니메이션 엔진 | `../reference/jquery-plugins/GSAP-3.12.2/dist/gsap.min.js` (+ 플러그인 개별 파일) |
| 타이핑 효과 | `../reference/jquery-plugins/unityping-0.1.0/dist/jquery.unityping.min.js` |
| 텍스트 효과 | `textillate-0.4.0` |

---

## 8. 실시간 통신

| 용도 | 경로 |
|------|------|
| WebSocket 폴백 | `../reference/jquery-plugins/sockjs-client-main/dist/sockjs.min.js` |
| STOMP | `../reference/jquery-plugins/stompjs-develop/bundles/stomp.umd.min.js` |
| AI 채팅(DWR) | `reference/jquery-plugins/dwr` + `arms/js/common/dwrChat.js` (`dwr_login()`) |
| 공동 편집(CRDT) | `bundle.yjs.js` |

---

## 9. 테마 / 대형 정적 도구

| 폴더 | 성격 |
|------|------|
| `reference/lightblue4/` | **운영 테마.** `docs/css/application.min.css`, `docs/js/app.js`, `docs/lib/*`. 신규 UI 는 이 테마의 클래스 체계(`widget`, `page-header`, `sidebar`)를 따른다 |
| `reference/light-blue/` | 구버전 템플릿. 컴포넌트 마크업 참고용(일부 lib 은 실제 로드됨) |
| `reference/bootstrap-3.4.1/` | Bootstrap 3 원본 — 그리드/유틸 기준 |
| `reference/drawio/`, `drawio-wiki/`, `drawdb/`, `gojs/`, `three.js-r165/` | **임베드 전용.** 내부 파일을 편집하지 않는다. 업그레이드는 통째 교체 |

`reference/jquery-plugins/jquery-easyui-1.10.16` 도 존재하지만 현재 앱 코드에서 쓰이지 않는다(문서에도 미기재).

---

## 10. 기능 → 라이브러리 빠른 표

| 구현할 기능 | 쓸 것 |
|-------------|-------|
| 토스트 알림 | jNotify (`jSuccess`/`jError`/`jNotify`) — 이미 전역 로드됨 |
| 목록 그리드 | dataTables 1.10.16 + `dataTable_build()` |
| 트리 | jstree v.pre1.0 + `jsTreeBuild()` |
| 칸반 | jkanban 1.3.1 |
| 간트 | frappe-gantt 0.6.1 |
| 캘린더 | fullcalendar 6.1.15 |
| 일반 차트 | ECharts 5.5.0 |
| 커스텀 시각화 | D3 6.7.0 (+ d3-sankey) |
| 엑셀형 시트 | jspreadsheet-ce 4.13.1 |
| 셀렉트 | select2 4.0.2 / 다중은 multiple-select 1.5.2 |
| 날짜·시간 | datetimepicker 2.5.20 |
| 폼 검증 | parsleyjs (lightblue4 번들) |
| 파일 업로드 | blueimp jQuery-File-Upload |
| PDF 보기 | pdf.js 3.11.174 |
| 버전 diff | diff2html 2.12.2 |
| 화면 캡처 | html2canvas 1.4.1 |
| 슬라이더 | swiper 11.1.4 |
| 온보딩 투어 | tourguide-js (전역 로드 + `tgGroup.js`) |
| 실시간 | sockjs + stompjs |
