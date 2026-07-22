# Result — frontend-expert / landing-calendar-redesign (구현)

수정 파일 1개: `Java-Service-Tree-Framework-Frontend-Web/arms/html/landing_calendar/content-container.html`

## 변경 요약
- 전체를 `.arms-cal-wrap` + `--cal-*` 토큰(accent #6366f1 외 5종, indigo 계열 신규) 으로 감쌈.
- 헤더 `.arms-cal-header.glass` 승격: business header CSS(3px 액센트 보더 + radial glow + eyebrow/title/subtitle) 포팅. h5→.cal-eyebrow, h1 유지+.cal-title, p→.cal-subtitle. 인라인 스타일→클래스.
- `#landing_calendar_lang_wrap`(label+select+4 option) 마크업 그대로 헤더 우상단 flex 배치, 다크 톤만 적용(option 배경 #1e293b).
- 카드 `section.widget`→`section.widget.glass`. h4 아이콘+widget_title 유지, `.gradient_middle_border` display:none(마크업 유지), blockquote(guide) indigo 좌측보더 유지.
- FullCalendar `<style>` 선택자 유지·값만 다크 glass 치환(§4 표 그대로). now-indicator만 cyan(--cal-accent-3). --fc-event-* indigo, --fc-page-bg-color transparent. 라이트 하드코드색 잔존 없음.
- 반응형 ≤991px: 헤더 세로 스택+언어셀렉터 order:-1, 캘린더 overflow-x:auto. @media print는 glow만 숨김.

## 보존 확인
- id 불변: #landing_calendar_view, #landing_calendar_lang, #landing_calendar_lang_wrap.
- data-lc-i18n 6키 보존: lang_label/eyebrow/title/description/widget_title/guide. 태그·텍스트 유지.
- option en/ko/zh/ja 순서·값·라벨 동일.
- JS 무접촉: landing_calendar.js는 getElementById("landing_calendar_view")·#landing_calendar_lang·.widget(widgster)·[data-lc-i18n] 순회에만 의존 → .body 하위 특정 DOM 구조 의존 없음 확인.
- business 마케팅 CSS/2단 TOC 미차용.

## Issues / Caveats
- indigo #6366f1 이 landing_ai 등 형제와 시각 충돌 가능 → 리뷰 단계 대조 권장(대체 blue #3b82f6 / violet #7c3aed).
- JS `buildMockEvents()`가 목업 이벤트에 구글 계열 하드코드색(#1a73e8 등) 지정 — JS 로직이라 무접촉. 완전 통일 원하면 별도 작업.
