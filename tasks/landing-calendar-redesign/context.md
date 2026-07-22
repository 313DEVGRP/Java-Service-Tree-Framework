# Context — landing-calendar-redesign

## 대상
- 파일: `Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html`
- 현재: 라이트 테마 미니멀. `<style>` 블록 + FullCalendar 마운트(`#landing_calendar_view`) + 언어 셀렉터(`#landing_calendar_lang`) + eyebrow/title/description + `.widget` 카드 1개.

## 공통 디자인 시스템
- landing_* 페이지들은 다크 **glass** 디자인 공유. 정의: `arms/css/common.css`의 `.glass`.
- 전형 구조(예: landing_business): `.arms-<x>-wrap` 래퍼 → 페이지별 CSS 변수 액센트 → `.arms-<x>-header.glass`(eyebrow/title/subtitle + KPI) → `.widget.glass` 카드들. `widget-controls`는 display:none.
- 참조 후보: landing_business(teal #2dd4bf), landing_function, landing_price, landing_introduce 등. 모두 `content-container.html` + `content-header.html` 보유. landing_calendar는 content-header.html 없음.

## 보존 필수 (기능)
- FullCalendar 초기화 JS (별도 JS 파일에서 `#landing_calendar_view` 마운트 추정 — 마크업 id 유지)
- `#landing_calendar_lang` select 및 option(en/ko/zh/ja)
- 모든 `data-lc-i18n="landing_calendar.*"` 속성/키

## 흐름
1. claude-main: 캘린더 성격에 맞는 참조/액센트/레이아웃 방향 제안 (result.md)
2. frontend-expert: 제안대로 content-container.html 재디자인
3. claude-main: 어울림 리뷰 → 개선점 도출
4. (필요 시) frontend-expert: 재수정
5. Verification → log.md
