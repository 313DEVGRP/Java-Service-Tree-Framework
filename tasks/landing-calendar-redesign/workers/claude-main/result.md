# Result — claude-main / landing-calendar-redesign (디자인 방향 제안)

## 1. 참조 페이지 선정 + 근거

**주 참조: `landing_business` (teal glass 표준 구조)** — `.arms-<x>-wrap` → 스코프 CSS 변수 액센트 → `.arms-<x>-header.glass`(eyebrow/title/subtitle) → `.widget.glass` 카드의 정본 패턴을 가장 명확히 구현. 차용: wrap(max-width 1280 중앙정렬), header(왼쪽 액센트 보더 + radial glow + eyebrow/title/subtitle), `.widget.glass > header`(액센트 그라디언트+아이콘) 골격만. 미차용: KPI 그리드·2단 sticky TOC·value/compare/plan/roi 마케팅 섹션(캘린더는 단일 도구 화면).

**보조 참조: `landing_function`** — 단일 도구/위젯 중심 화면에서 `.widget.glass` 단독 사용(TOC 없는 단순 레이아웃) 실례.

## 2. 액센트 컬러 제안

캘린더 성격(시간·일정·계획)에 맞춰 **indigo/blue 계열**을 스코프 토큰으로 신규 지정(네이밍 규약 `--<prefix>-accent`는 그대로 준수).

```css
.arms-cal-wrap {
    --cal-accent:    #6366f1;  /* indigo — 계획·시간, 캘린더 관습색 */
    --cal-accent-2:  #a5b4fc;  /* hover/보조 텍스트 밝은 톤 */
    --cal-accent-3:  #22d3ee;  /* '오늘'/now-indicator 강조 포인트(cyan) */
    --cal-accent-4:  #fbbf24;  /* 경고/기타(필요시만) */
    --cal-text:      #cbd5e1;
    --cal-text-mute: #94a3b8;
}
```

근거: (a) business teal과 구분되어 페이지 정체성 유지, (b) indigo는 캘린더 UI 관습색, (c) cyan을 "오늘/현재시각"에만 배분해 기능적 의미 전달.

## 3. 레이아웃 / 마크업 구조 제안

기존 3블록(언어셀렉터·헤더·widget)을 wrap 한 겹으로 감싸고, 헤더를 glass 헤더 문법으로 승격, 카드를 `.widget.glass`로 승격(신규 구조 발명 없이 재배치).

```
.arms-cal-wrap
├── .arms-cal-header.glass
│     ├── #landing_calendar_lang_wrap  ← 기존 그대로, 헤더 우상단 배치
│     │     └── label[data-lc-i18n=lang_label] + select#landing_calendar_lang(en/ko/zh/ja)
│     ├── p.cal-eyebrow   [data-lc-i18n=landing_calendar.eyebrow]
│     ├── h1.cal-title    [data-lc-i18n=landing_calendar.title]   ← h1 유지
│     └── p.cal-subtitle  [data-lc-i18n=landing_calendar.description]
└── .col-lg-12 (또는 .arms-cal-body)
      └── section.widget.glass
            ├── header > h4 > <i class="fa fa-calendar"></i> + span[data-lc-i18n=widget_title]
            └── .body
                  ├── .gradient_middle_border   ← display:none (마크업은 유지)
                  ├── blockquote[data-lc-i18n=guide]   ← 보조 정보로 유지
                  └── #landing_calendar_view           ← FullCalendar 마운트 id 불변
```

규칙: `#landing_calendar_lang_wrap` 삭제/재작성 금지(헤더 우상단 flex 배치). 헤더 인라인 스타일 → 클래스(`.cal-eyebrow/.cal-title/.cal-subtitle`)로 이동하되 data-lc-i18n 키·텍스트·태그 유지. `widget-controls`는 원본에 없으므로 신규 추가 금지. wrap `max-width:1280px; margin:0 auto`.

## 4. FullCalendar 다크 테마 오버라이드 방향

기존 `#landing_calendar_view` 스타일 블록(구글 라이트: #fff/#3c4043/#e0e0e0)은 삭제하지 말고 **선택자 유지·값만 다크 glass 톤 치환**(회귀 위험 최소).

| 대상 | 현재값 | glass 다크 치환 |
|---|---|---|
| `#landing_calendar_view` 배경 | `#fff` | `transparent` 또는 `rgba(255,255,255,.02)` |
| `.fc-toolbar-title` | `#3c4043` | `#f1f5f9` |
| `.fc-button-primary` 배경/텍스트 | 흰/짙은 | `rgba(255,255,255,.04)` / `var(--cal-text)`, border `rgba(255,255,255,.12)` |
| 버튼 hover | `#f1f3f4` | `rgba(99,102,241,.10)` |
| 버튼 active | `#e8f0fe`/`#1a73e8` | `rgba(99,102,241,.16)` + `var(--cal-accent)` |
| `--fc-border-color` | `#e0e0e0` | `rgba(255,255,255,.10)` |
| `--fc-today-bg-color`/today 셀 | `#fef7e0` | `rgba(99,102,241,.10)` |
| now-indicator line/arrow | `#ea4335` | `var(--cal-accent-3)` cyan |
| col-header/slot-label cushion | `#70757a` | `var(--cal-text-mute)` |

추가 최소 보강: `--fc-event-bg-color`/`--fc-event-border-color` indigo 계열, `--fc-page-bg-color:transparent`. 라이트 하드코드색 전수 치환. i18n·id·로직 무접촉.

## 5. frontend-expert 전달 구현 지시 요약

- 최상위 `<div class="arms-cal-wrap">`로 감싸고 `--cal-*` 토큰(§2) 정의. business `--bz-*` 복붙 금지.
- 헤더 `.arms-cal-header.glass`로 승격: business header CSS(3px 액센트 보더 + radial glow eyebrow/title/subtitle)를 `--cal-*`로 포팅. eyebrow=h5→`.cal-eyebrow`, title=h1 유지+`.cal-title`, desc=p→`.cal-subtitle`. data-lc-i18n 키 4개 전부 보존.
- `#landing_calendar_lang_wrap`(label+select+4 option) 마크업 그대로 헤더 우상단 배치. id 불변.
- 카드 `section.widget`→`section.widget.glass`. header h4 아이콘+`widget_title` 유지. `.gradient_middle_border` display:none. blockquote(guide) 유지.
- **`#landing_calendar_view` div·id 절대 불변** (FullCalendar 마운트).
- 기존 `#landing_calendar_view` `<style>` 블록: 선택자 유지·값만 다크 glass 치환(§4). 라이트 하드코드색 잔존 금지. now-indicator만 cyan.
- business 마케팅 CSS(KPI/TOC/value/compare/plan/roi/phase/partner/cta)·2단 그리드·sticky TOC 가져오지 말 것.
- `@media print`·반응형(≤991px 헤더/셀렉터 줄바꿈, 캘린더 가로 오버플로우 방지) 최소만.
- JS 파일·i18n 사전·option 값·태그 종류 변경 금지.

## 6. Verification Checklist

- [ ] output_format 6개 섹션 일치
- [ ] 참조 파일 경로 실재
- [ ] task.md constraints(기능·i18n 보존, 마케팅 섹션 배제, 기존 클래스/토큰 규약) 충족
- [ ] Do NOT(코드 직접 수정·기능/i18n 변경·타 페이지 수정) 위반 없음

## Issues / Caveats

- **가정 1**: FullCalendar 초기화 JS는 별도 파일·`#landing_calendar_view` id 마운트로 추정. frontend-expert는 해당 JS를 열어 `.body` 하위 특정 구조 의존이 없는지 1회 확인 권장.
- **가정 2**: indigo 신규 지정. family 내 indigo 사용 형제(landing_ai 등)와 시각 충돌 가능 — 리뷰 단계에서 landing_ai·landing_devtools 색과 대조. 충돌 시 blue(#3b82f6)/violet(#7c3aed) 대체.
- 참조 landing_business는 1898행 중 1223행까지 확인(차용 골격 L1~250에 전부 포함, 판단 영향 없음).
