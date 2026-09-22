# Context — REQ-MAPPING-FUNC-01

## 현재 상태

완료(status: done). 폴더 유실 후 재구성본.
산출물 = `artifacts/fe-be_mapping-gaps.csv` 1,014행 (FE→BE없음 52 · BE→호출없음 962) +
`artifacts/fe-be_mapping-gaps.xlsx` 단일 시트. AC 8항목 전부 통과, codex-critic 리뷰만 공백.

## 핵심 정보

- 입력(경로만): `tasks/req-backend-func-01/artifacts/backend-core_endpoints_flat.csv`(383행),
  `tasks/req-frontend-func-01/artifacts/frontend-web_api-calls_flat.csv`(540행)
- 생산 로직 정본: `.claude/skills/api-catalog/scripts/fe_be_gaps.py` · `sheets_xlsx.py` · `tree_actions.py`
  실행 = `CATALOG_TASK`·`CATALOG_BE_CSV`·`CATALOG_FE_CSV` 환경변수
- 대조 열쇠 = `sources/gateway-rules.md`. `api` 세그먼트여도 Middle-Proxy 가 직접 처리하는 4개 basePath 가 있다
- 상속 판별은 백엔드 카탈로그 `kind=inherited` 행의 경로 suffix 23종에서 읽는다(손으로 적지 않는다)
- 메뉴명은 네비 라벨 → `html/<page>/content-header.html` → 공통 모듈 → 페이지 키 순, 출처는 `menusource`

## 미해결 이슈

- codex-critic 은 Codex 쿼터 소진(2026-10-13 회복) — 선행 2건도 같은 사유로 미수행
- `tasks/` 하위 파일이 사라지는 현상 2회 관측(xlsx 2개 / 이 폴더 전체). 원인 미상

## 참조 자료

- sources/requirement.md · sources/request.md · sources/gateway-rules.md
