# Result — frontend-expert / landing_calendar i18n 리뷰

> frontend-expert(2계층 도메인 서브에이전트) 리뷰 원문. agentId: aa7dc3a28ef63fb0b

## ① 총평: 조건부 승인 (수정 요청 1회 필요)

설계 방향(전역 서버팩이 zh 미지원·3개 언어뿐 → data-locale 마크업만 재사용, 문자열은 페이지-로컬 사전)은 타당·근거 정확. FullCalendar `globalLocales=[]`로 기존 `locale:"ko"` 실질 미동작 진단, zh→zh-cn 매핑, 쿠키 재사용도 코드 검증 시 사실.

단 원본 재확인 결과 result.md가 표면화하지 못한 회귀 위험 2건(전역 bindLocaleText 이중 바인딩 충돌, locales-all.global.js 경로 오류 가능성)이 있어, 그대로 적용 시 미동작·콘솔 경고·깜빡임 발생. 2건 반영해야 승인 가능.

## ② 발견 항목

### 🔴 [필수-1] 전역 bindLocaleText와의 이중 바인딩 충돌
- 근거: common.js `로드_완료_이후_실행_함수()`→`loadLocale()`→`changeLocale()`→`setLocale()`(async:false)→`bindLocaleText()`(common.js:2448)가 모든 `[data-locale]` 순회. 이 함수는 `loadPluginGroupsParallelAndSequential()`의 .then()에서 호출되며, 그건 landing_calendar.js:100 execDocReady()가 직접 부르는 함수.
- 결과: 신규 키(landing_calendar.title 등)는 서버팩·/arms/locales/*.json에 없음 → 전역 bindLocaleText가 "국제화 문자열 없음" 경고 5+회 + applyLandingLocale과 같은 노드 이중 처리 순서 경쟁(깜빡임).
- 제안(권장 A): 페이지-로컬 사전은 data-locale이 아닌 전용 속성(data-lc-i18n) 또는 전용 클래스로 스코프해 전역 querySelectorAll("[data-locale]")와 분리. (대안 B: data-locale 유지 + applyLandingLocale을 전역 loadLocale 이후 실행 + 신규 키를 /arms/locales에 추가 — 단 zh 누락·jp/ja 불일치 잔존 → A 권장)

### 🔴 [필수-2] locales-all.global.js 로드 경로 미명시 → 404 위험
- 근거: 기존 로드는 `dist/index.global.js`. 그러나 locales-all.global.js는 dist/에 없고 `packages/core/`에만 존재(검증). 경로 유추 시 404 → 로케일 미로드.
- 검증: packages/core/locales-all.global.js는 `(function(index_js){…})(FullCalendar)` 래퍼로 전역 globalLocales에 push → index.global.js 이후 같은 그룹 순차 로드 시 정상.
- 제안: 경로 명시 + index.global.js와 같은 그룹 배열 내 뒤에 순차 배치(별도 병렬 그룹이면 FullCalendar 미정의 에러).

### 🟡 [권장-1] ja vs jp 파일명 불일치
- arms/locales/는 en/jp/ko.json인데 매핑은 ja. 대안 B 채택 시 ja 폴백이 jp.json 못 찾음. A안이면 문서화만.

### 🟡 [권장-2] 언어 셀렉터 이원화
- landing-navigation.html에 이미 전역 스위처(ko/ja/en, changeLocale) 존재(:752~791,1160). 별도 4개국 select 추가 → 한 페이지 스위처 2개·언어집합 3 vs 4 공존.
- 제안: 셀렉터 change 시 changeLocale 호출 말 것(전역은 zh→ko 정규화로 zh 깨짐). 쿠키만 setCookie + 페이지-로컬 applyLandingLocale 처리 확인.

### 🟢 [선택-1] buttonText 하드코딩 제거 부수효과
- today/week/day 라벨이 로케일 기본값으로 대체 → 목업 표기 변경, 검수자 공지 권장.

### 🟢 [선택-2] result.md 완결성
- diff 원문이 파일로 없음("대화 로그 참조") → 최종 반영본을 artifacts/에 diff로 보존 권장.

## ③ claude-main 앞 수정 요청서 (1회분)

- [필수-1] data-locale 전역 충돌 회피: 페이지-로컬 사전은 전역 bindLocaleText(common.js:2448, querySelectorAll("[data-locale]"))와 겹치지 않게 전용 속성/클래스로 스코프.
- [필수-2] locales-all 경로·순서 고정: 경로를 `../reference/jquery-plugins/fullcalendar-6.1.15/packages/core/locales-all.global.js`로 명시 + index.global.js와 같은 그룹 배열 내 그 뒤 순차 배치.
- [권장-2] 셀렉터 격리: change 핸들러는 changeLocale() 호출 말고 setCookie("locale",…)만 + applyLandingLocale() 처리.
- [선택] 최종 반영본(HTML 전체+JS diff)을 tasks/landing-calendar-i18n/artifacts/에 diff로 보존.

## ④ Verification Checklist (워커 자체 보고)

- [x] output_format 준수, 파일 직접 수정 없음
- [x] 수정 요청 1회 한정·우선순위 분류
- [x] 리뷰 범위(다국어 한정) 준수
- [x] 원본 대조: content-container.html, landing_calendar.js(locale/buttonText/pluginGroups), common.js(changeLocale allowlist·bindLocaleText·로드완료 트리거)
- [x] 기술 주장 실물 검증: dist globalLocales=[], locales-all은 packages/core/에만, 전역 스위처 존재, 폴백 en/jp/ko.json
- [x] Do NOT 위반 없음
