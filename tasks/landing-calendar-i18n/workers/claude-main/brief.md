# Brief — claude-main / landing_calendar 다국어(i18n) 지원 추가

## Worker 행동 규약 (고정 — 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Objective

landing_calendar 페이지에 en/ko/zh/ja 4개 언어 언어팩 기능을 추가한다(문자열 분리 + 언어 전환 + FullCalendar locale 연동).

## Input

```
task:    tasks/landing-calendar-i18n/task.md
context: tasks/landing-calendar-i18n/context.md
대상:    Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html
```

## Constraints

- 스택 준수: vanilla JS · jQuery · Bootstrap · FullCalendar. 새 프레임워크·빌드 단계 금지
- 하드코딩 문자열(제목·설명·UI 라벨)을 언어팩 사전으로 분리
- FullCalendar 요일·버튼 등 로케일을 선택 언어와 연동
- 캘린더 초기화 JS가 이 파일에 없으면 발굴 시도, 부재 시 가정 명시(Caveats)
- 언어 선택 UI 위치/저장 방식은 기존 프로젝트 패턴 우선, 없으면 합리적 기본 + 근거

## Output Format

- result 저장: `tasks/landing-calendar-i18n/workers/claude-main/result.md` (Orchestrator가 저장)
- 구조: ① 접근 요약 ② 변경 코드 = fenced diff 또는 전체 파일(경로 명시) ③ 언어팩 사전(en/ko/zh/ja) ④ Assumptions/Caveats ⑤ Verification Checklist 4항목

## Do NOT

- 파일 직접 쓰기 금지 (텍스트 반환 → Orchestrator가 저장)
- 요청 밖 리팩토링·기능 추가 금지
- 기존 레이아웃·스타일 회귀 유발 금지
