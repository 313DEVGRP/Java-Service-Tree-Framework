# REQ-FRONTEND-FUNC-01 — Frontend-Web API 호출 목록 추출

## 메타

```yaml
status: done
created: 2026-09-21
updated: 2026-09-21
priority: high
```

## Goal

`arms/js/` · `backoffice/js/` 의 js 가 호출하는 REST API 를 전수 추출해 메뉴·파일 단위 플랫 CSV 1본을 `artifacts/` 에 만든다.
완료 조건 = ① `/` 로 끝나는 api 0건 ② 모든 행에 menuname · jsfilename · apiurl ③ arms·backoffice 양쪽 포함.

## Constraints

- 읽기 전용. 대상 저장소 수정 금지, 코드 실행(빌드·서버 기동) 금지
- 레퍼런스 산출물이다. 구조 비평·결함 지적·개선 권고 금지
- 설명 문단을 늘리지 않는다. 표로 표현할 수 있으면 표로 한다
- 소스에 없는 엔드포인트를 지어내지 않는다. 복원 불가 URL 은 사유를 적는다

## Acceptance Criteria

- [x] `artifacts/` 에 CSV 1본 존재 (540행). 헤더 `menuname,area,jsfile,line,httpMethod,apiurl,callPattern,note`
- [x] apiurl 이 `/` 로 끝나는 행 0건
- [x] arms/js · backoffice/js 양쪽 포함 (arms 418 / backoffice 122)
- [x] 필수 3컬럼 공란 0건 (메뉴 미연결은 사유 라벨 5종으로 구분)
- [x] task.md constraints 위반 없음 (평가문·권고문 없음)

## Worker Plan

```yaml
workers_approved:
- worker: claude-main
  approved_at: 2026-09-21
  purpose: js API 호출 전수 추출·URL 복원·메뉴 매핑 스펙/코드 (실행 주체 = 서브에이전트 frontend-expert)
  approved_by: user (via /REQ-RUN)
  target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
  write_scope: tasks-only
- worker: codex-critic
  approved_at: 2026-09-21
  purpose: 산출 CSV 를 소스 대조로 리뷰 (누락·미복원 URL·컬럼 충족)
  approved_by: user (via /REQ-RUN)
  target_repo: /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
  write_scope: none

planned_workers:
- role: claude-main
  purpose: 생산 (frontend-expert 서브에이전트로 실행)
- role: codex-critic
  purpose: 리뷰
```

## Context Snapshot

엑셀 3행을 `/REQ-RUN` 으로 변환한 작업. 원문 = `sources/requirement.md`, 요청문 = `sources/request.md`.
대상 js 169개, 호출 패턴 `$.ajax` 409 · `$.get` 30 · `fetch(` 8 · `$.post` 1.
메뉴↔페이지 매핑은 `arms/html/template/page-navigation.html` (page= 링크 30종), 라우팅은 `template.html?page={page}` ↔ `js/{page}.js` 1:1.

## Notes

- **codex-critic 리뷰 미수행** — Codex 사용량 한도 소진(2026-10-13 회복). Acceptance Criteria 는 Orchestrator 자체 대조로 전부 통과했으나 제3자 리뷰는 비어 있다. 재개 명령은 `workers/codex-critic/result.md` 참조.
- 산출물: `artifacts/frontend-web_api-calls_flat.csv` (540행) + `_flat.xlsx`(단일 시트). 생성기는 `.claude/skills/api-catalog/scripts/front_calls.py`
- 알려진 한계: 조건부 쿼리스트링 `+=` 변형이 부분적으로만 전개됨 (`workers/codex-critic/result.md` 참조)
- 선행 작업 REQ-BACKEND-FUNC-01(`tasks/req-backend-func-01/`) 의 산출물이 Backend-Core 엔드포인트 정본 — 프론트 URL 대조에 쓸 수 있으나 이번 요구사항의 완료 조건은 아니다
