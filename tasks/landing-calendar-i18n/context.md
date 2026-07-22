# Context — landing_calendar 다국어(i18n) 지원 추가

## 현재 상태

task 정의 완료(pending). claude-main brief 작성 단계. 아직 worker 미호출.

## 핵심 정보

- 대상 파일: `Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html`
- 페이지 구성: `<style>` 오버라이드 + 소개 섹션(h5 "Weekly Schedule" / h1 "주간 캘린더" / p 설명) + FullCalendar 위젯(`#landing_calendar_view`) + blockquote 안내문
- 스택: vanilla JS · jQuery · Bootstrap · FullCalendar (서버렌더링/MPA). 새 빌드 단계 없음
- 캘린더 초기화 JS는 이 파일에 없음(외부/공통 스크립트 추정) — claude-main이 발굴하거나 부재 시 가정 명시
- 하드코딩 문자열: "Weekly Schedule", "주간 캘린더", 설명 p, "Weekly Calendar", blockquote 안내문

## 미해결 이슈

- 언어 선택 UI 위치·형태(셀렉트 박스 vs 버튼 그룹) — claude-main 판단, 기존 UI 패턴 우선
- 언어 상태 저장 방식(localStorage vs URL param) — 기존 프로젝트 규약 확인 후 결정
- FullCalendar locale 파일 로딩 방식 — 기존 로딩 방식 확인

## 참조 자료

- tasks/landing-calendar-i18n/task.md
- Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html
