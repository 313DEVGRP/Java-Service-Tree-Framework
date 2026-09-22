# REQ-MAPPING-FUNC-01 — FrontEnd-Backend API 매핑 분석

## 메타

```yaml
status: done
created: 2026-09-21
updated: 2026-09-22
priority: high
```

## Goal

Frontend-Web 호출과 Backend-Core 엔드포인트를 게이트웨이 경로 규칙으로 대조해
**매핑되지 않는 것만** 추린 CSV 1본 + 엑셀 1본(한 시트, menuname 정렬)을 `artifacts/` 에 만든다.
완료 조건 = ① 게이트웨이 규칙으로 추론 대조, 애매하면 note ② 미매핑만 수록
③ menuname 에 추정 표현 0건(js↔html 1:1, 출처는 menusource) ④ 상속 URL 이 provider 로 구분.

## Constraints

- 읽기 전용. 대상 저장소·엑셀 수정 금지, 코드 실행 금지
- 레퍼런스 산출물이다. 구조 비평·결함 지적·개선 권고 금지
- 설명 문단을 늘리지 않는다. 표로 표현할 수 있으면 표로 한다
- 두 입력 CSV 에 없는 URL 을 지어내지 않는다
- 상속 액션 목록·메뉴명을 손으로 적지 않는다 (카탈로그·html 구조에서 읽는다)

## Acceptance Criteria

- [x] `artifacts/` 에 CSV 1본 + 엑셀 1본(한 시트). 헤더에 menuname · backendurl · frontendurl · 판정 · provider 포함
- [x] 매핑 성립 행이 CSV 에 없다 (미매핑만)
- [x] 양방향 포함: `FE→BE없음` / `BE→호출없음`
- [x] menuname 에 `추정` 표현 0건, `menusource` 공란 0건
- [x] 상속 URL 이 `provider = 상속(<부모클래스>)` 로 구분. 프론트가 Tree CRUD 를 부르는 호출도 동일 표기
- [x] `api` 세그먼트지만 Middle-Proxy 가 처리하는 구간이 note 에 명시
- [x] 집계 정합 (프론트 540 = 대조 + 대상 외 / 백엔드 360 + 821 − 오버라이드 = 호출됨 + 미호출)
- [x] task.md constraints 위반 없음 (평가문·권고문 없음)

## Worker Plan

```yaml
workers_approved:
- worker: claude-main
  approved_at: 2026-09-22
  purpose: 대조 스펙·정규화 규칙 (실행 주체 = 서브에이전트 frontend-expert)
  approved_by: user (via /REQ-RUN)
  target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework
  write_scope: tasks-only
- worker: codex-critic
  approved_at: 2026-09-22
  purpose: 매핑 판정 리뷰 (오탐·미탐·메뉴명 정확성)
  approved_by: user (via /REQ-RUN)
  target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework
  write_scope: none

planned_workers:
- role: codex-critic
  purpose: 리뷰
```

## Context Snapshot

입력은 선행 두 작업의 산출물 — `tasks/req-backend-func-01/artifacts/backend-core_endpoints_flat.csv`(383행),
`tasks/req-frontend-func-01/artifacts/frontend-web_api-calls_flat.csv`(540행).
생산 로직은 `.claude/skills/api-catalog/scripts/` 로 이관돼 있다 (`fe_be_gaps.py` · `sheets_xlsx.py` · `tree_actions.py`).

## Notes

- **2026-09-22 폴더 유실 후 재구성.** 이전 실행(2026-09-21)의 task.md·log.md·context.md·briefs·results 가
  폴더째 사라져 복구 불가(`tasks/*` 는 .gitignore 대상, 휴지통에도 없음). 산출물은 스킬 스크립트로 재생성.
- 이번 실행은 엑셀 4행 보완판(규칙 4개 추가) 기준. 그 규칙은 이미 스킬 스크립트에 구현돼 있어
  생산 워커 재호출 없이 재생성·검증만 수행 (`log.md` [DECISION] 참조)
- 산출물: `artifacts/fe-be_mapping-gaps.csv` (1,014행, menuname 정렬) · `artifacts/fe-be_mapping-gaps.xlsx` (단일 시트 `data`)
- **codex-critic 리뷰 미수행** — Codex 쿼터 소진(2026-10-13 회복). AC 8항목은 Orchestrator 자체 대조로 통과, 미탐 전수 확인은 공백
