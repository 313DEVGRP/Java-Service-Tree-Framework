# Brief — claude-main / landing-function-license-flow

## Worker 행동 규약 (고정 — 모든 brief에 그대로 유지, 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Execution Context

```yaml
target_repo: C:/DEV/sourcecode/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web
write_scope: none     # 쓰기 금지. 설계 텍스트만 반환 — 반영은 Orchestrator
```

## Objective

`landing_function` 페이지를 라이선스 타입(POC·PRO·ENT)별 액션 흐름 화면으로 재구성하는
정보구조 설계 + 스타일 매핑표를 확정한다. HTML 구현은 후행 워커 담당.

## Input

```
tasks/landing-function-license-flow/  task.md · context.md
  sources/requirement-REQ-LANDING-FUNC-01.md   요구사항 원문 (7단계·검증기준)
  sources/style-recon.md                       팔레트·토큰 관례 정찰
<target_repo>/arms/css/common.css              정본 CSS
<target_repo>/arms/html/landing_poc|landing_price/   관례 참고
```

## Constraints

- `style-recon.md` 팔레트·`--<page>-*` 토큰 관례 준수. 상한 아니므로 직접 재확인
- 신규 색상값 금지. 정찰 팔레트 내에서만 `--lf-*` 토큰 정의
- POC만 7단계 상세. PRO·ENT는 골격까지
- JIRA 연동·백엔드 API 실구현 설계 금지 (화면 표현 범위)

## Output Format

Markdown 텍스트 반환. 5섹션:

1. 화면 정보구조 — 섹션 순서, POC 7단계 제목·설명·시각 표현
2. 스타일 매핑표 — `--lf-*` → 팔레트 값 → 출처 페이지. 재사용 클래스 포함
3. 입출력 표현 — JIRA Admin 접속정보 / 4관점 리포트·KPI·주간보고 배치
4. PRO·ENT 골격
5. Issues/Caveats

## Do NOT

- 파일 쓰기·수정
- 기존 `landing_function/content-container.html`을 근거로 삼기 (요구사항이 무시 지시)
- 새 색상값·디자인 시스템 도입
- HTML 전문 작성
