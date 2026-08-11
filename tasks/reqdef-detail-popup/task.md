# 요구사항 정의 엑셀 업로드 — 상세 내용 팝업

## 메타

```yaml
status: done
created: 2026-08-10
updated: 2026-08-10
priority: medium
```

## Goal

요구사항 정의 엑셀 업로드 탭의 목록에서 요구사항명을 클릭하면 공용 팝업이 열리고,
해당 행의 `상세 내용`이 CKEditor(읽기 전용)로 렌더링된다.

## Constraints

- target_repo: `C:\Users\www\IdeaProjects\Java-Service-Tree-Framework\Java-Service-Tree-Framework-Frontend-Web`
- 백엔드 변경 금지 — `GET /auth-user/api/arms/reqAdd/excel-upload/req-def/pd-service-id/{id}` 응답의
  `data.detail`(ReqDefDataVO.detail)이 이미 내려오므로 프론트만 수정한다.
- 간트 엑셀 업로드 탭의 기존 동작을 건드리지 않는다.
- 팝업 범위는 페이지 로컬 공용 모달 (사용자 선택). 전역 template 파티션은 만들지 않는다.
- CKEditor는 읽기 전용 (사용자 선택).

## Acceptance Criteria

- [x] `#reqdef_statustable`의 요구사항명 셀이 상세 내용이 있는 행에 한해 클릭 가능
- [x] 클릭 시 `#reqDetailModal`이 열리고 헤더에 요구사항명, 본문에 상세 내용이 표시됨
- [x] 상세 내용은 `CKEDITOR.instances["reqdef_detail_editor"]`로 렌더링 (readOnly, toolbar 없음)
- [x] 엑셀 원문의 개행이 유지되고, HTML 특수문자가 이스케이프되어 스크립트 주입이 발생하지 않음
- [x] 팝업은 페이지 로컬 공용 함수 `openReqDetailPopup(title, detailText)`로 열리며,
      다른 탭/테이블에서도 같은 모달을 재사용할 수 있다

## Worker Plan

```yaml
# 외부 worker 미사용. Orchestrator 내부 추론만으로 수행 (승인 불필요).
workers_approved: []
planned_workers: []
```

## Context Snapshot

- 화면: `arms/html/reqAddExcelUpload/content-container.html` (탭 `#tabReqDef`) +
  `arms/js/reqAddExcelUpload.js` (`renderReqDefFilteredTable`)
- 데이터: `ReqDefRowVO.data.detail` ← 엑셀 `상세 내용` 컬럼 (`ReqDefDataVO`)
- 참조 패턴: 제품 관리 상세보기 탭 —
  `arms/js/pdService.js:114` `CKEDITOR.replace("stats_pdservice_detail_editor", { skin: "office2013" })`
  → `arms/js/pdService.js:722` `.setData(json.c_contents)`
- 모달 마크업 관례: `modal fade` + `modal-content modalDarkBack`
  (예: `arms/html/reportSWOT/content-container.html:386`)
- CKEditor는 `arms/template.html:253`에서 전역 로드됨
