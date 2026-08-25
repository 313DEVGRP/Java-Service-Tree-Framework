# Context — landing-function-license-flow

## 현재 상태

작업 정의 완료(`status: pending`). 워커 승인 대기 — `workers_approved`가 비어 있어 호출 금지 상태.

## 핵심 정보

- 요구사항: REQ-LANDING-FUNC-01 「A-RMS 기능 페이지 개선」, 진행현황 `기획중`, 우선순위 High
- 대상: `Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_function/`
  (`content-container.html` 53KB · `content-header.html` 515B — 기존 구현, 참고하지 않음)
- 스타일 정본: `arms/css/common.css`, 형제 `landing_*` 폴더 30개
- 핵심 요구: 라이선스 타입(POC·PRO·ENT)별 실제 액션 흐름 표시. POC는 7단계
- 검증 기준이 곧 스타일 제약 — 기존 CSS 전수 확인 후 통일성 유지
- 모듈에 `CLAUDE.md`·`AGENTS.md` 없음 → 루트 `CLAUDE.md`와 기존 코드 관례를 따른다

## 미해결 이슈

- (해소 2026-08-25) 기존 `content-container.html` 53KB → **전면 대체** 확정 (사용자 결정)
- (해소 2026-08-25) reviewer 슬롯 공석 → 검증은 Orchestrator 소스 실측. 제3자 검증은 미충족으로 남김
- PRO·ENT 흐름 상세: 요구사항에 POC만 7단계 기술됨. 이번 범위는 골격까지
- Cost 관점 색상 `#a78bfa`는 근거 있는 추론(landing_index에 Time·Scope·Resource만 색 명시)

## 참조 자료

- sources/requirement-REQ-LANDING-FUNC-01.md
- ../요구사항_TASK_전환_Format.md
- ../요구사항_TASK_전환_Sample.md
