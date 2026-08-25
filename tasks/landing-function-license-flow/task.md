# landing-function-license-flow

## 메타

```yaml
status: reviewing
created: 2026-08-24
updated: 2026-08-25
priority: high
requirement_id: REQ-LANDING-FUNC-01
```

## Goal

A-RMS 기능 페이지(`landing_function`)를 라이선스 타입(POC·PRO·ENT)별 실제 액션 흐름을 보여주는
화면으로 개선한다. POC 흐름은 ①JIRA 연결 → ②Default 프로젝트 Base Version 설정 →
③매핑 이슈의 타입별 우선순위·유형 확인 → ④요구사항 이슈 선정(EPIC/label 등) → ⑤A-RMS 자동 수집
→ ⑥Time·Scope·Resource·Cost 관점 분석 결과 → ⑦개인 성과지표·주간 보고 리포트의 7단계로 표현한다.
완료 조건 = ① POC 7단계 흐름이 화면에서 순서대로 읽힌다 ② `common.css` 및 기존 `landing_*`
구현에서 쓰인 CSS를 전수 확인해 색감·컴포넌트가 통일된다 ③ 입력(JIRA Admin 접속 정보)과
출력(4관점 리포트·개인 KPI·주간 보고)이 화면상 명시된다.

## Constraints

- 기존 `landing_function/` 구현은 참고하지 않고 새로 구성 (요구사항 `[작업 대상]` 지시)
- `common.css`·기존 `landing_*` HTML의 CSS를 **먼저 전수 확인**한 뒤 스타일 결정.
  새 색상·새 디자인 토큰 임의 도입 금지
- PRO·ENT는 이번 범위에서 화면 골격까지. 7단계 상세 흐름은 POC 타입만
- 백엔드 API·JIRA 연동 실구현 금지 (화면 표현 범위)
- 워커 산출물 반영은 Orchestrator가 수행. 워커의 대상 모듈 직접 쓰기 금지

## Acceptance Criteria

- [ ] POC 7단계 흐름이 화면에 순서대로 표현됨
- [ ] `common.css` + 기존 `landing_*` CSS 전수 확인 근거가 result에 제시됨 (파일 목록·재사용 클래스)
- [ ] 색감·컴포넌트가 기존 랜딩 페이지와 통일 (신규 색상 토큰 0)
- [ ] 입력(JIRA Admin 접속정보)·출력(4관점 리포트·개인 KPI·주간 보고) 화면 명시
- [ ] PRO·ENT 골격 존재
- [ ] 대상 모듈 작업트리가 Orchestrator 반영 전까지 clean (워커 직접 쓰기 없음)

## Worker Plan

```yaml
# 모든 worker는 사용 전 승인 필요. 비어있으면 호출 금지.
workers_approved:
- worker: claude-main
  approved_at: 2026-08-25
  purpose: 라이선스 타입별 액션 흐름 정보구조·화면 구성 설계 + 기존 CSS 기반 스타일 매핑표 확정
  approved_by: user
- worker: ollama
  approved_at: 2026-08-25
  purpose: 설계안 보조 검증 — 요구사항 7단계 누락·순서 오류 점검
  approved_by: user

planned_workers:
- role: claude-main
  purpose: 라이선스 타입별 액션 흐름 정보구조·화면 구성 설계 + 기존 CSS 기반 스타일 매핑표 확정 (strategist)
- role: ollama
  purpose: 설계안 보조 검증 — 요구사항 7단계 누락·순서 오류 점검 (reviewer, 자체호스팅)
```

`[Worker Settings]` 원문: MainWoker=claude-main / SubWorker=ollama / MainWoker-SubAgent=frontend-expert.
`frontend-expert`는 2계층 도메인 서브에이전트로 승인 게이트 밖이지만, 실제 호출 비용이 발생하므로
투명성 차원에서 여기에 병기한다 (`_shared/learnings.md` [2026-07-22] 교훈).

- subagent: frontend-expert — 확정된 설계·스타일 매핑표 기반 HTML/CSS 구현 (게이트 밖, 호출 사실 log에 기록)

## Context Snapshot

대상: `Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_function/`
(`content-container.html` 53KB, `content-header.html` 515B — 둘 다 기존 구현, 참고하지 않음)
스타일 정본: `arms/css/common.css` + 형제 `landing_*` 30개 폴더.
진행 현황 `기획중`이나 `[작업 대상]`이 실제 경로를 지정하므로 설계와 구현 diff를 모두 산출한다.

## Notes

- 비고 "지속적인 갱신이 전제" → 이번 작업은 REQ-LANDING-FUNC-01 현재 판(2026-08-24 발췌) 기준.
  요구사항 갱신 시 별도 작업으로 분리
- `[제약 조건 / 비기능 요구사항]`이 N/A이므로 Constraints는 `[작업 대상]`·`[검증 기준]`·
  시스템 규약에서 도출 (Format.md §2 "금지 → 제약" 규칙)
- 소분류 빈칸 → 경로는 `[작업 대상]` 지정값 사용
- 원문 발췌: `sources/requirement-REQ-LANDING-FUNC-01.md`
