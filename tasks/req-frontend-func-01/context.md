# Context — REQ-FRONTEND-FUNC-01

## 현재 상태

완료(status: done). 산출물 = `artifacts/frontend-web_api-calls_flat.csv` 540행
(호출 지점 458 / distinct apiurl 382 / js 81개 / arms 418·backoffice 122 / 말미 `/` 0건).
codex-critic 리뷰만 미수행 — Codex 쿼터 소진(2026-10-13 회복), Orchestrator 자체 대조로 대체.

## 핵심 정보

- 대상: `Java-Service-Tree-Framework-Frontend-Web/arms/js/` · `backoffice/js/` — js 169개
- 산출: 메뉴·파일 단위 API 플랫 CSV 1본 → `artifacts/`
- 호출 패턴 실측: `$.ajax` 409 · `$.get` 30 · `fetch(` 8 · `$.post` 1
- 메뉴 매핑: `arms/html/template/page-navigation.html` 의 `page=` 링크 30종.
  라우팅은 `template.html?page={page}` 이고 `js/{page}.js` 와 1:1 (docs/ai/03_directory_structure)
- 검증 기준 ①(`/` 로 끝나는 api 0건)은 문자열 조합 URL 을 끝까지 복원했는지를 재는 지표다.
  예: `url: "/arms/reqAdd/" + id` 를 그대로 적으면 위반.

## 미해결 이슈

- codex-critic 제3자 리뷰 공백 (쿼터 회복 2026-10-13). 재개 명령은 `workers/codex-critic/result.md` 하단.
- 조건부 쿼리스트링 `+=` 변형 부분 전개 — 한계로 기록, 미보정.
- (해소) backoffice 메뉴 정의 = `backoffice/html/template/page-sidebar.html` (16 링크)

## 참조 자료

- sources/requirement.md (엑셀 원문 = 변경 감지 기준선)
- sources/request.md (7줄 요청문)
- Java-Service-Tree-Framework-Frontend-Web/docs/ai/03_directory_structure/frontend-web-directory.md
- workers/claude-main/result.md (채택본) · workers/claude-main/extract_api_calls.py (변환 코드 원본)
- artifacts/frontend-web_api-calls_flat.csv (최종 산출물)
