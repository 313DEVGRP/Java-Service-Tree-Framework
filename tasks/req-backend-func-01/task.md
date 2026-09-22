# REQ-BACKEND-FUNC-01 — Backend-Core REST API 목록 추출

## 메타

```yaml
status: done
created: 2026-09-21
updated: 2026-09-21  # v2 (추출기 수정 재생성)
priority: high
```

## Goal

Backend-Core 의 REST 엔드포인트 전수를 컨트롤러별로 플랫하게 나열한 CSV 1본을 `artifacts/` 에 만든다.
완료 조건 = ① 자체 선언 엔드포인트가 빠짐없이 기재 ② 상속 엔드포인트가 1회만 기재되고 상속 컨트롤러가 열거됨
③ 각 행에 controller class name · rest end point · package name 이 채워짐.

## Constraints

- 읽기 전용. 대상 저장소·엑셀 수정 금지, 코드 실행(빌드·테스트) 금지
- 레퍼런스 산출물이다. 구조 비평·결함 지적·개선 권고 금지
- 설명 문단을 늘리지 않는다. 표로 표현할 수 있으면 표로 한다
- CSV·JSON 에 없는 엔드포인트를 지어내지 않는다 (수치 정본은 `sources/`)

## Acceptance Criteria

- [x] `artifacts/` 에 CSV 1본 존재, 헤더에 controller class name · rest end point · package name 포함
- [x] 자체 선언 엔드포인트 수가 추출기 집계와 일치 (실측 360, 컨트롤러 92 — SKILL.md 기준값 359 는 이전 실측치, log [DECISION] 참조)
- [x] 상속 엔드포인트가 컨트롤러마다 반복되지 않고 1회 기재 + 상속 컨트롤러 열거 컬럼 존재
- [x] task.md constraints 위반 없음 (평가문·권고문 없음)

## Worker Plan

```yaml
workers_approved:
- worker: claude-main
  approved_at: 2026-09-21
  purpose: Backend-Core 엔드포인트 전수 추출·플랫 CSV 생성 (실행 주체 = 서브에이전트 backend-expert)
  approved_by: user (via /REQ-RUN)
  target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core
  write_scope: tasks-only
- worker: codex-critic
  approved_at: 2026-09-21
  purpose: 산출 CSV 를 소스 대조로 리뷰 (누락·중복·컬럼 충족 여부)
  approved_by: user (via /REQ-RUN)
  target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core
  write_scope: none

planned_workers:
- role: claude-main
  purpose: 생산 (backend-expert 서브에이전트로 실행)
- role: codex-critic
  purpose: 리뷰
```

## Context Snapshot

엑셀 `요구사항정의서_엑셀양식_v3_1_3.xlsx` 2행을 `/REQ-RUN` 으로 변환한 작업.
원문 = `sources/requirement.md`, 요청문 = `sources/request.md`.
추출 도구는 기존 스킬 `.claude/skills/api-catalog` (상속 전개 포함). 기준값 표가 SKILL.md 에 있다.

## Notes

- 시트 `[Worker Settings]` 의 `MainWorker-SubAgent` 에 frontend-expert 도 있으나 이번 범위가 Backend-Core 단독이라 호출하지 않음 (`log.md` [DECISION] 참조)
- **codex-critic 리뷰 미수행** — Codex 사용량 한도 소진(2026-10-13 회복). Acceptance Criteria 는 Orchestrator 자체 대조로 전부 통과했으나 제3자 리뷰는 비어 있다. 재개 명령은 `workers/codex-critic/result.md` 참조.
- 산출물(v2, 채택본): `artifacts/backend-core_endpoints_flat.csv` (383행) · `artifacts/backend-core_endpoints_flat.xlsx`(단일 시트)
- 재현: `python3 artifacts/build_backend_catalog.py` (그 앞단은 `.claude/skills/api-catalog/scripts/expand_inherit.py`)
