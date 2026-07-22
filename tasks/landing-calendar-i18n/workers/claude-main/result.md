# Result (v2 — frontend-expert 리뷰 반영) — claude-main / landing_calendar i18n

> claude-main 워커 원문(v2). agentId af8fad21212d91a0c. v1은 이 파일 git 히스토리 참조.

## ① 무엇을 바꿨는지 요약 (v1 대비)

리뷰 지적 3건 모두 반영. common.js 소스 대조 재확인.

1. **[필수-1] 전역 data-locale 바인딩 충돌 회피** — 페이지-로컬 i18n 요소 속성을 `data-locale`→`data-lc-i18n`. execDocReady가 부르는 loadPluginGroupsParallelAndSequential 완료 콜백이 로드_완료_이후_실행_함수(common.js:669)→loadLocale(:509)→bindLocaleText(:2448) 항상 실행, 이 함수가 querySelectorAll("[data-locale]")(:2449)로 전체 순회. 신규 키가 서버팩/arms/locales에 없어 경고+깜빡임. 전용 속성으로 완전 격리. bindLandingText 셀렉터도 [data-lc-i18n]로 수정.

2. **[필수-2] locales-all 경로·순서 고정** — dist/에 없음(확인). packages/core/locales-all.global.js에만 존재, (function(index_js){…})(FullCalendar) 래퍼로 globalLocales에 push. index.global.js와 같은 그룹 배열 내 바로 뒤 순차 배치(v1은 별도 배열 → 병합).

3. **[권장-2 + 추가발견] 셀렉터·저장소 격리 강화** — v1은 공통 쿠키 locale 재사용했으나, 재검증 중 더 깊은 회귀 발견: loadLocale()이 로드마다 changeLocale(getCookie("locale")) 실행, changeLocale allowlist가 ["ko","ja","en"]뿐이라 zh를 ko로 정규화 후 쿠키 덮어씀(:2409,:2416). 즉 공통 쿠키에 zh 저장 시 다음 로드에서 전역이 파괴. 해결: 페이지 전용 저장키 `landing_calendar_lang`로 분리(setCookie/getCookie 헬퍼는 유지, 키만 교체). change 핸들러는 changeLocale() 미호출.

사전(en/ko/zh/ja) 내용은 v1과 동일. 키 이름도 동일, 참조 속성만 data-lc-i18n.

## ② 변경 코드

실제 적용됨(Orchestrator가 반영). 요약:
- **content-container.html**: `<style>`에 셀렉터 CSS 추가 / 소개 섹션에 언어 셀렉터 블록 추가 / 5개 문자열 + label = 6곳에 `data-lc-i18n` 속성
- **arms/js/landing_calendar.js**: LANDING_SUPPORTED_LANGS·LANDING_LANG_COOKIE·LANDING_FC_LOCALE·LANDING_I18N 사전 / getLandingLang·bindLandingText([data-lc-i18n])·bindLandingLangSelector·applyLandingCalendarLocale / buildMockEvents 사전화 / pluginGroups에 locales-all 순차 추가 / 초기 locale=LANDING_FC_LOCALE 매핑 / buttonText 하드코딩 제거 / execDocReady에 bindLandingText+bindLandingLangSelector 호출

## ③ 사전 (en/ko/zh/ja)

v1과 동일 (LANDING_I18N). UI 라벨 6키 + event.* 7키 × 4개 언어. FullCalendar 로케일 en→en, ko→ko, zh→zh-cn, ja→ja.

## ④ Assumptions / Caveats (갱신)

- [해소] 전역 i18n 충돌: data-lc-i18n 전용 속성으로 common.js bindLocaleText([data-locale] 순회)와 완전 분리.
- [해소·강화] zh 저장 안전성: 전용 키 landing_calendar_lang 사용. loadLocale→changeLocale allowlist(ko/ja/en)의 zh→ko 정규화·덮어쓰기 원천 회피. 전역 스위처(ko/ja/en)와 이 페이지 언어(en/ko/zh/ja)는 독립 상태로 공존.
- **트레이드오프(의도)**: 위 분리로 전역 스위처 변경이 이 페이지에 자동 반영 안 됨(반대도 동일). zh 미지원·서버팩 부재 제약 하 회귀 회피 목적. 향후 통합 시 백엔드 zh 팩 + 4키 + changeLocale allowlist 확장 별도 필요.
- [권장-1 확인] /arms/locales/는 en/jp/ko.json만(ja·zh 없음, 파일명 jp). 본 구현은 전역 JSON/서버팩 미의존이라 무관.
- FullCalendar 로케일: dist globalLocales=[] 확인 → packages/core/locales-all.global.js를 index.global.js와 동일 그룹·순차 로드로 실제 공급. zh→zh-cn(간체), 번체 필요 시 LANDING_FC_LOCALE.zh="zh-tw" 한 줄.
- buttonText 하드코딩 제거 유지(로케일 객체 자동 제공). XSS: 정적 문자열 + textContent → sanitize 불필요.

## ⑤ Verification Checklist (워커 자체 보고)

- [x] output_format 일치
- [x] 참조 경로 실존(content-container.html, landing_calendar.js, packages/core/locales-all.global.js, common.js:507/509/2401/2407/2448/2449)
- [x] task.md constraints 충족
- [x] Do NOT 위반 없음(파일 직접 안 씀·전역 common.js 미변경·요청 3건 외 리팩토링 없음)
