[2026-08-10 00:00] [DECISION] 코드베이스에 "공통 팝업" 컴포넌트가 없음을 확인. 각 화면이 `modal fade` + `modal-content modalDarkBack` 마크업을 개별 선언하는 관례만 존재 (reportSWOT/swotReqDetailModal, aiChat/ragTextModal 등).
[2026-08-10 00:00] [DECISION] 사용자 선택 — 팝업 범위는 "페이지 로컬 공용 모달", CKEditor 는 "읽기 전용".
[2026-08-10 00:00] [DECISION] 외부 worker 미사용. Orchestrator 내부 추론만으로 수행 (승인 게이트 비대상).
[2026-08-10 00:00] [DECISION] 백엔드 무변경. `ReqDefDataVO.detail` 이 이미 `GET /excel-upload/req-def/pd-service-id/{id}` 응답의 `data.detail` 로 직렬화됨 (ReqAddController.java:569).
[2026-08-10 00:00] [CHANGE] arms/html/reqAddExcelUpload/content-container.html — `#reqDetailModal` 추가 (헤더 `#reqDetailModalTitle`, 본문 `#reqdef_detail_editor`).
[2026-08-10 00:00] [CHANGE] arms/js/reqAddExcelUpload.js — `reqDetailTextToHtml` / `openReqDetailPopup` / `shown.bs.modal` CKEditor 지연 생성 추가, `renderReqDefFilteredTable` reqName 렌더러에 `a.reqdef-detail-link` 링크 + tbody 클릭 위임 핸들러 추가.
[2026-08-10 00:00] [CHANGE] arms/css/reqAddExcelUpload/reqAddExcelUpload.css — `.reqdef-detail-link` 스타일 추가.
[2026-08-10 00:00] [VERIFICATION] `node --check arms/js/reqAddExcelUpload.js` → JS SYNTAX OK
[2026-08-10 00:00] [VERIFICATION] HTML id 존재 확인 → reqDetailModal / reqDetailModalTitle / reqdef_detail_editor 모두 OK
[2026-08-10 00:00] [VERIFICATION] JS 심볼 존재 확인 → openReqDetailPopup / reqdef-detail-link / reqDetailTextToHtml / shown.bs.modal 모두 OK
[2026-08-10 00:00] [VERIFICATION] `readOnly: true` 는 arms/js/adms/editor-operation.js:20 에서 이미 쓰이는 기존 패턴. CKEditor 4.22.1.
[2026-08-10 00:00] [VERIFICATION] 미실행 — 브라우저 실제 구동 검증(앱 기동 + 엑셀 업로드 후 클릭)은 백엔드 기동이 필요해 수행하지 못함. 사용자 확인 필요.
[2026-08-10 00:00] [NOTE] 기존 코드가 reqName/detail 을 이스케이프 없이 테이블 셀에 넣고 있으나(`wrap()`), 사전 존재 이슈라 손대지 않음. 팝업 본문은 신규 코드이므로 `$("<div>").text(t).html()` 로 이스케이프함.
[2026-08-10 00:00] [FIX] 사용자 확인 중 발견 — (1) 팝업 왼쪽 160px 공백: arms/css/override.css:537 `.control-label { float: left; width: 160px; }` 전역 규칙 탓으로 label 제거. (2) 상단 줄: `toolbar: []` 은 빈 툴바 막대를 그림 → `removePlugins: "toolbar,elementspath,resize"` + `height: 420` 으로 교체.
[2026-08-10 00:00] [VERIFICATION] node --check 통과, content-container.html 내 control-label 잔여 0건.
[2026-08-10 00:00] [FIX] ckeditor/config.js:8 의 전역 `removePlugins = "exportpdf"` 가 인스턴스 config 에 의해 통째로 뎮여쓰여 exportpdf 가 되살아나는 문제 발견. removePlugins 목록에 exportpdf 재명시.
[2026-08-10 00:00] [FIX] 회귀 원인 확인 — ckeditor.js 의 clipboard 플러그인이 requires:"dialog,notification,toolbar" 로 toolbar 를 다시 로드한다. removePlugins 로는 못 뺀다. config.toolbar 가 undefined 이면 기본 전체 툴바가 자동 생성되어 오히려 더 많이 노출됨.
[2026-08-10 00:00] [FIX] toolbar: [] 복구 + removePlugins 에서 toolbar 제외, 빈 .cke_top/.cke_bottom 은 #reqDetailModal 스코프 CSS 로 display:none 처리.
