# Brief — frontend-expert / landing-calendar-redesign

## 행동 규약 (고정)
- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지
- 외과수술식 수정: 기존 스타일 유지, 무관 코드 비접촉
- 불확실·불일치는 결과 보고의 Issues/Caveats에 표면화

## Objective
claude-main 디자인 방향(result.md)대로 landing_calendar/content-container.html를 glass 다크 디자인으로 재구성한다. 기능·i18n 100% 보존.

## Input (직접 Read)
- 대상: Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html (직접 수정)
- 방향: tasks/landing-calendar-redesign/workers/claude-main/result.md
- 참조: Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_business/content-container.html
- 공통: Java-Service-Tree-Framework-Frontend-Web/arms/css/common.css (.glass)

## 핵심 지시 (result.md §5 요약)
- `.arms-cal-wrap` 래퍼 + `--cal-*` 토큰(accent #6366f1, accent-3 #22d3ee 등) 정의
- 헤더 `.arms-cal-header.glass` 승격 (eyebrow/title(h1)/subtitle), 언어셀렉터 우상단 배치
- 카드 `section.widget` → `section.widget.glass`
- `#landing_calendar_view` `<style>` 블록: 선택자 유지·값만 다크 glass 톤 치환, now-indicator만 cyan
- business 마케팅 CSS/2단 TOC 가져오지 말 것

## 보존 필수 (변경 금지)
- `#landing_calendar_view` div·id (FullCalendar 마운트)
- `#landing_calendar_lang` select·4 option(en/ko/zh/ja)
- 모든 `data-lc-i18n` 속성/키, 텍스트, 태그 종류
- 외부 JS·i18n 사전 비접촉. 먼저 FullCalendar 초기화 JS를 찾아 `.body` 하위 특정 구조 의존이 없는지 1회 확인.

## Output
- 대상 파일 직접 수정 (write_scope: 해당 1개 파일)
- 완료 후 변경 요약(무엇을/왜)과 보존 확인 결과를 텍스트로 반환

## Do NOT
- 기능/i18n 변경, 다른 페이지 수정, JS 로직 변경
- 마케팅 섹션(KPI/비교표/plan 등) 추가
