# Brief — claude-main / landing-calendar-redesign

## Worker 행동 규약 (고정 — 삭제 금지)

- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 사용자 대화 채널 없음: 가정은 명시하고, 불확실·불일치는 result의 Issues/Caveats에 표면화

## Objective

landing_calendar 페이지를 landing_* 공통 glass 디자인 시스템에 통일시키기 위한 **디자인 방향(참조 페이지·액센트·레이아웃 구조)** 을 제안한다.

## Input

```
task:    tasks/landing-calendar-redesign/task.md
context: tasks/landing-calendar-redesign/context.md
대상 파일: Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html
참조 후보: Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_business/content-container.html (teal glass 표준 구조)
           그 외 landing_* 형제 페이지들, arms/css/common.css 의 .glass
```

## Constraints

- 기능 100% 보존 전제: FullCalendar 마운트 `#landing_calendar_view`, 언어 셀렉터 `#landing_calendar_lang`, 모든 `data-lc-i18n` 키. 이 위에 얹을 디자인만 제안.
- 캘린더는 "일정 도구" 성격 → KPI/가격/비교표 같은 마케팅 섹션은 억지로 넣지 말 것. 캘린더에 어울리는 최소 구조(헤더 + glass 위젯 내 캘린더 + 보조 정보)로.
- landing_* 실제 클래스/CSS 변수 패턴을 그대로 활용(신규 디자인 언어 발명 금지).

## Output Format

- 파일 위치: `tasks/landing-calendar-redesign/workers/claude-main/result.md`
- 형식: Markdown
- 구조:
  1. 참조 페이지 선정 + 근거 (1~2개)
  2. 액센트 컬러 제안 (CSS 변수값 + 캘린더 성격상 근거)
  3. 레이아웃/마크업 구조 제안 (래퍼·헤더·위젯 구성, 어떤 기존 클래스를 쓸지)
  4. FullCalendar 다크 테마 오버라이드 방향 (기존 라이트 톤 → glass 톤)
  5. frontend-expert에게 전달할 구현 지시 요약 (bullet)
  6. Verification Checklist

## Do NOT

- 코드 파일 직접 수정 금지 (제안만)
- 기능/i18n 변경 제안 금지
- 다른 페이지 수정 제안 금지
