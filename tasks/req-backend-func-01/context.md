# Context — REQ-BACKEND-FUNC-01

## 현재 상태

완료(status: done). 채택본 = `artifacts/backend-core_endpoints_flat.csv` 383행 + `backend-core_endpoints_flat.xlsx`(단일 시트)
(자체 선언 360 + 상속 부모매핑 23, 상속 전개 실인스턴스 821, 도달 가능 합계 1181).
codex-critic 리뷰만 미수행 — Codex 쿼터 소진(2026-10-13 회복), Orchestrator 자체 대조로 대체.

## 핵심 정보

- 대상: Backend-Core (`Java-Service-Tree-Framework-Backend-Core/src/main/java`)
- 산출: 엔드포인트 플랫 CSV 1본 → `artifacts/`
- 추출 도구는 이미 있다: `.claude/skills/api-catalog` — `expand_inherit.py` 가
  `sources/endpoints_expanded.csv`(HTTP·path·controller·javaMethod·출처·선언파일·line)를 낸다.
  package name 컬럼은 선언파일 경로에서 유도해 덧붙여야 한다.
- 상속 주의: 컨트롤러 92 중 58개가 TreeAbstractController 상속.
  grep 으로 `@*Mapping` 만 세면 3배 틀린다. 이번 요구사항은 상속분을 컨트롤러마다 반복하지 말고
  **공통 매핑 1회 + 상속 컨트롤러 열거**로 낸다 (검증 기준 ②).
- 기준값(2026-09-21 실측, SKILL.md): 컨트롤러 92 · 자체 선언 359 · 상속 전개 821 · 합계 1,180

## 미해결 이슈

- codex-critic 제3자 리뷰 공백. 재개 명령은 `workers/codex-critic/result.md` 하단.

## 참조 자료

- sources/requirement.md (엑셀 원문 = 변경 감지 기준선)
- sources/request.md (7줄 요청문)
- .claude/skills/api-catalog/SKILL.md
- workers/claude-main/result.md (채택본 — 누락 감사·컬럼 스펙·변환 코드)
- artifacts/backend-core_endpoints_flat.csv (최종 산출물)
