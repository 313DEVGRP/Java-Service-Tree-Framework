# Brief — frontend-expert / landing_calendar 다국어(i18n) 지원 추가

## Worker 행동 규약 (고정 — 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Objective

claude-main이 작성한 언어팩(i18n) 구현을 리뷰하고, 변경할 점이 있으면 claude-main에 전달할 **수정 요청 1회분**을 정리한다.

## Input

```
task:            tasks/landing-calendar-i18n/task.md
context:         tasks/landing-calendar-i18n/context.md
리뷰 대상:        tasks/landing-calendar-i18n/workers/claude-main/result.md
원본 페이지:      Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html
```

## Constraints

- 리뷰 관점: jQuery/Bootstrap/FullCalendar 관례 부합, i18n 완전성(4개 언어·누락 문자열), 언어 전환·locale 연동 정확성, 접근성, 회귀 위험, unobtrusive JS
- 직접 코드 수정하지 말 것 — 이 흐름에서는 **리뷰 + 수정 요청 정리**만
- 수정 요청은 **1회로 한정**. 우선순위(필수/권장/선택)로 분류
- 문제 없으면 "수정 불필요"로 명시 (억지 지적 금지)

## Output Format

- result 저장: `tasks/landing-calendar-i18n/workers/frontend-expert/result.md` (Orchestrator가 저장)
- 구조: ① 총평(승인/조건부/수정필요) ② 발견 항목(파일·라인·근거·제안, 우선순위별) ③ claude-main 앞 수정 요청서(1회분, 없으면 "없음") ④ Verification Checklist

## Do NOT

- 새 기능·범위 확장 제안 금지 (요청은 다국어 언어팩 한정)
- 2회 이상 수정 요청 금지
- 원본 파일 직접 수정 금지
