# arms/html 언어팩 미적용 라벨 감사 리포트 (REQ-F-001)

- 작성: 2026-07-28 / worker: claude-main (strategist)
- 대상: `C:/DEV/sourcecode/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web` (read-only)
- 조사 범위: `arms/html/**` **HTML 164개 전량**, `arms/js/**` JS 121개(비-min 118개), `arms/locales/{ko,en,jp}.json`

---

## 1. 요약 (Executive Summary)

| 지표 | 값 |
|---|---|
| 조사 HTML | **164개 (전량)** |
| 추출 라벨(노출 문자열) | **9,643건** |
| `data-locale` 태깅 라벨 | **110건** |
| 미태깅 라벨 | **9,533건** |
| **속성 태깅 커버리지** | **1.14 %** |
| `data-locale` 보유 파일 | **6 / 164 (3.7 %)** |
| 사용 중 고유 키 | 54개 |
| 폴백팩에서 해소되는 키 | ko 22 / en 20 / jp 0 |
| **실효 커버리지(태깅 ∧ 값존재)** | **ko 0 % · en 0 % · jp 0 %** (§4 참조) |
| JS 하드코딩 한국어 문자열 | **1,833건 / 118 파일** |

**결론**: `arms/html`의 언어팩 적용은 사실상 부재하다. 라벨 9,643건 중 **98.9 %가 태깅조차 없고**, 태깅된 110건도 아래 3개 결함 때문에 **현재 런타임에서 어떤 언어로도 치환되지 않는다.**

**치명 결함 3건 (모두 코드 근거 확인)**

1. **`ko.json`이 유효하지 않은 JSON** — `arms/locales/ko.json:26`에 trailing comma(`"s": "SWOT 리포트",` 뒤 `},`). `$.ajax(dataType:"json")`가 파싱 실패 → `.done()` 미실행 → **한국어 폴백 전량 무효**.
2. **`ja` / `jp` 식별자 불일치** — `arms/js/common.js:2417`은 `allowedLocale = ["ko","ja","en"]`인데 파일명은 `jp.json`. 일본어 선택 시 `/arms/locales/ja.json`을 요청 → **404**. 게다가 `jp.json`은 **0바이트**.
3. **`data-locale` 키의 59 %가 어느 팩에도 없음** — 54개 키 중 ko 32개·en 34개 미정의. `bindLocaleText()`는 `console.warn`만 남기고 원문 유지(`common.js:2462-2465`).

즉 API가 살아 있을 때만 일부 동작하며, 폴백 경로는 3개 언어 모두 붕괴 상태다.

---

## 2. 판정 기준

### 2.1 메커니즘 (근거: `arms/js/common.js`)

```
loadLocale()  (common.js:509, 부트스트랩)
  └ changeLocale(locale)                       :2416   allowedLocale=["ko","ja","en"]
      └ setLocale(locale)                      :2430
          ├ 1차: GET /auth-anon/yml/language-config/packs/language/{locale}   (Global-Config API)
          │        └ bindLocaleText(result.languagePack)                      :2441
          └ 폴백(error): GET /arms/locales/{locale}.json → flattenObject()    :2444-2452
                   └ bindLocaleText(flattenObject(data))                      :2451

bindLocaleText(locales)                        :2457
  └ document.querySelectorAll("[data-locale]") :2458   ← 치환 대상은 이 속성뿐
       key = tag.dataset.locale
       undefined → console.warn 후 return (원문 유지)  :2462-2465
       HTML 포함 → innerHTML = sanitizeHTML(content)   :2466-2467
       placeholder 요소 → tag.placeholder = content     :2468-2469
       그 외 → tag.textContent = content                :2471
```

### 2.2 두 축 분리

감사는 두 축을 **독립적으로** 판정한다 (하나만 봐서는 오판).

- **축 ① 속성 태깅** — 해당 라벨에 `data-locale`이 있는가. 없으면 팩 내용과 무관하게 **구조적 미적용**(치환 시도조차 안 됨).
- **축 ② 언어별 값 존재** — 태깅된 키가 `ko/en/jp` 팩에 실제 값을 갖는가. 없으면 **키 누락**(태깅은 됐으나 원문 노출).

"적용 완료"는 **① ∧ ②** 를 모두 만족할 때만 성립한다.

### 2.3 라벨 범위

- 포함: 텍스트 노드, `placeholder`, `title`, `alt`, `<input type=button|submit|reset>`의 `value`, `<option>` 텍스트
- 제외: `<script>`·`<style>` 블록, HTML 주석, 숫자/기호/HTML 엔티티 단독 문자열
- 추출 스크립트: `artifacts/_audit.py` · `artifacts/_keys.py` (재현 가능)

---

## 3. 폴더별 집계 (라벨 수 상위 30 / 전체 69폴더)

`data-locale` 열이 0인 폴더는 해당 화면 라벨이 **전량 미적용**이다.

| # | 폴더 | html | 라벨 | data-locale | 미태깅 | 커버리지 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | landing_index | 2 | 589 | 0 | 589 | 0.0 % |
| 2 | **template** | 9 | 512 | **108** | 404 | **21.1 %** |
| 3 | analysisResource | 9 | 410 | 0 | 410 | 0.0 % |
| 4 | landing_contributors | 2 | 390 | 0 | 390 | 0.0 % |
| 5 | landing_business | 2 | 382 | 0 | 382 | 0.0 % |
| 6 | landing_company | 2 | 321 | 0 | 321 | 0.0 % |
| 7 | reqGantt | 2 | 300 | 0 | 300 | 0.0 % |
| 8 | landing_customerService | 2 | 286 | 0 | 286 | 0.0 % |
| 9 | landing_price | 2 | 275 | 0 | 275 | 0.0 % |
| 10 | analysisScope | 7 | 265 | 0 | 265 | 0.0 % |
| 11 | landing_wai | 2 | 257 | 0 | 257 | 0.0 % |
| 12 | analysisTime | 7 | 256 | 0 | 256 | 0.0 % |
| 13 | reqAdd | 2 | 249 | 0 | 249 | 0.0 % |
| 14 | landing_ai | 2 | 246 | 0 | 246 | 0.0 % |
| 15 | analysisCost | 6 | 226 | 0 | 226 | 0.0 % |
| 16 | landing_canyon | 2 | 211 | 0 | 211 | 0.0 %* |
| 17 | landing_privacy | 2 | 210 | 0 | 210 | 0.0 % |
| 18 | landing_devtools | 2 | 199 | 0 | 199 | 0.0 % |
| 19 | detail_dashboard | 2 | 192 | 0 | 192 | 0.0 % |
| 20 | jiraServer | 2 | 191 | 0 | 191 | 0.0 % |
| 21 | detail_kpi | 2 | 187 | 0 | 187 | 0.0 % |
| 22 | kpi | 2 | 186 | 0 | 186 | 0.0 % |
| 23 | landing_effect | 2 | 181 | 0 | 181 | 0.0 % |
| 24 | searchEngine | 2 | 178 | 0 | 178 | 0.0 % |
| 25 | landing_check | 2 | 171 | 0 | 171 | 0.0 % |
| 26 | landing_function | 2 | 166 | 0 | 166 | 0.0 % |
| 27 | pdService | 2 | 159 | 0 | 159 | 0.0 % |
| 28 | landing_policy | 2 | 147 | 0 | 147 | 0.0 % |
| 29 | landing_provision | 2 | 146 | 0 | 146 | 0.0 % |
| 30 | reportKPI | 2 | 146 | 0 | 146 | 0.0 % |
| — | *(나머지 39폴더)* | 68 | 1,905 | 2 | 1,903 | 0.1 % |
| | **합계** | **164** | **9,643** | **110** | **9,533** | **1.14 %** |

\* landing_canyon은 `data-locale`이 0이지만 **독자 KO/EN 스킴**을 별도 보유 — §6.2 참조.

**`data-locale` 보유 6개 파일 (전체 태깅의 100 %)**

| 파일 | 태깅 수 |
|---|---:|
| `arms/html/template/page-navigation.html` | 47 |
| `arms/html/template/landing-navigation.html` | 32 |
| `arms/html/template/page-sidebar.html` | 26 |
| `arms/html/template/page-header.html` | 3 |
| `arms/html/mapping/content-container.html` | 1 |
| `arms/html/reportWeekly/content-container.html` | 1 |

태깅은 **공유 내비게이션 템플릿에만** 존재한다. 개별 업무 화면(요구관리·분석·리포트·설정)의 본문 라벨은 **한 건도 태깅되지 않았다**.

---

## 4. 언어별 커버리지 (축 ②)

사용 중 고유 키 54개를 각 팩과 대조한 결과.

| 로케일 | 파일 | 파일 상태 | 정의 키 | 54키 중 해소 | 미해소 | 런타임 실효 |
|---|---|---|---:|---:|---:|---|
| ko | `arms/locales/ko.json` | **INVALID JSON** (L26 trailing comma) | 22 (수리 시) | 22 | 32 | **0 %** — 파싱 실패로 전량 무효 |
| en | `arms/locales/en.json` | 정상 | 21 | 20 | 34 | 태깅분 20건만 (전체의 0.2 %) |
| jp | `arms/locales/jp.json` | **0바이트** + 파일명 불일치(`ja` 요청) | 0 | 0 | 54 | **0 %** |

### 4.1 키 해소 상세 (54키 요약)

| 구분 | 키 수 | ko | en | jp |
|---|---:|---|---|---|
| `nav.*` (내비 공통) | 28 | 22 해소 / 6 누락 | 20 해소 / 8 누락 | 0 |
| `menu-nav.*` (사이드바) | 16 | **전량 누락** | **전량 누락** | 0 |
| `landing.menu.*` (랜딩 메뉴) | 8 | **전량 누락** | **전량 누락** | 0 |
| `category.state.title` / `common.btn.btn_cancel` | 2 | **누락** | **누락** | 0 |

- `menu-nav.*` 16키·`landing.menu.*` 8키·기타 2키 = **26키(48 %)는 어느 팩에도 정의가 없다.** 태깅 헛수고 상태.
- `nav.language.{ko,ja,en}` 3키도 양쪽 팩 모두 누락 — **언어 전환 메뉴 자체가 미번역**.
- `nav.requirement.g` / `nav.requirement.k`: ko만 존재, en 누락 → 영어에서 간트/칸반 메뉴가 한글로 노출.
- 반대로 `nav.analysis.g`는 **en에만 정의되고 HTML에서 미사용** (유일한 orphan 키).
- `nav.alm.m`, `nav.requirement.a`, `nav.requirement.e`: 태깅됐으나 양쪽 팩 누락.

### 4.2 jp 판정 (두 축 분리 표기)

일본어 미적용은 **두 원인이 중첩**되어 있어 구분해 기록한다.

- **키 누락 축**: `jp.json`이 0바이트 → 정의 키 0개. 54키 전부 미해소.
- **경로 결함 축**: `common.js:2417`이 `"ja"`를 허용값으로 쓰므로 요청 URL은 `/arms/locales/ja.json`. **파일명이 `jp.json`이라 404** — 설령 `jp.json`을 채워도 폴백 경로로는 로드되지 않는다.

→ jp는 "번역 미작성"과 "로더 결함"을 **함께** 고쳐야 한다. 파일만 채우는 조치로는 해결되지 않는다.

---

## 5. 대표 사례 (경로:라인 — 전수 아님)

### 5.1 태깅 O · 값 X (원문 그대로 노출)

| 경로:라인 | 키 | 원문 | ko | en |
|---|---|---|---|---|
| `arms/html/template/page-navigation.html:255` | `menu-nav.gantt` | (간트) | X | X |
| `arms/html/template/page-navigation.html:361` | `menu-nav.swot-report` | (SWOT 리포트) | X | X |
| `arms/html/template/page-header.html:48` | `nav.language.ko` | 한국어 | X | X |
| `arms/html/template/page-header.html:63` | `nav.language.ja` | 日本語 | X | X |
| `arms/html/template/page-header.html:78` | `nav.language.en` | English | X | X |
| `arms/html/template/landing-navigation.html:764` | `nav.language.ko` | 한국어 | X | X |
| `arms/html/mapping/content-container.html:7` | `category.state.title` | `A-RMS 상태별 ALM 상태 매핑` | X | X |

### 5.2 태깅 O · 값 O (그러나 ko는 파싱 실패로 무효)

| 경로:라인 | 키 | ko 값 | en 값 |
|---|---|---|---|
| `arms/html/template/page-navigation.html:128` | `nav.product.p` | 제품 관리 | Product Manage |
| `arms/html/template/page-navigation.html:570` | `nav.product.p` | 제품 관리 | Product Manage |
| `arms/html/template/page-sidebar.html` (`nav.report.s` 5회) | `nav.report.s` | SWOT 리포트 | SWOT Report |

### 5.3 빈 요소 — 키 미해소 시 공백 렌더

| 경로:라인 | 내용 |
|---|---|
| `arms/html/reportWeekly/content-container.html:494` | `<span data-locale="common.btn.btn_cancel"></span>` — **원문 텍스트가 없음**. 키가 양쪽 팩에 미정의이므로 `bindLocaleText`가 return하여 **버튼 라벨이 영구 공백**. 다른 사례는 원문 폴백이 되지만 이 건은 즉시 UI 결함. |

### 5.4 태깅 X (구조적 미적용) — 라벨 최다 화면

| 경로 | 라벨 수 |
|---|---:|
| `arms/html/landing_index/content-container.html` | 584 |
| `arms/html/landing_contributors/content-container.html` | 385 |
| `arms/html/landing_business/content-container.html` | 378 |
| `arms/html/landing_company/content-container.html` | 317 |
| `arms/html/reqGantt/content-container.html` | 294 |
| `arms/html/landing_customerService/content-container.html` | 281 |
| `arms/html/landing_price/content-container.html` | 270 |
| `arms/html/landing_wai/content-container.html` | 252 |
| `arms/html/reqAdd/content-container.html` | 243 |
| `arms/html/landing_ai/content-container.html` | 241 |

---

## 6. JS 주입 문자열 (별도 축 — `data-locale`로 해결 불가)

### 6.1 규모

| 지표 | 값 |
|---|---:|
| 한국어 포함 JS(비-min) | **118 파일** |
| 고유 한국어 문자열 리터럴 | **1,833건** |
| DOM 주입/알림 패턴 라인 | 243건 |

**`currentLanguagePack`은 기록되지만 어디서도 읽히지 않는다.** `common.js:19`에서 선언, `:2439-2440`에서 대입되며 그 외 참조 지점이 없다 → **JS 런타임 문자열에는 i18n 조회 경로가 아예 존재하지 않는다.** 이 1,833건은 `data-locale` 태깅만으로는 절대 해결되지 않으며, 별도의 조회 API(`t(key)` 등)가 신설되어야 한다.

한국어 리터럴 상위 파일: `aiSupport.js`(887) · `landing_calendar.js`(858) · `detail_dashboard.js`(539) · `kpi.js`(524) · `reqAdd.js`(395) · `aiChat.js`(390) · `jiraServer.js`(377) · `reqStatus.js`(353) · `detail_kpi.js`(350) · `reqGantt.js`(328).

**패턴 유형별 대표 사례**

| 유형 | 경로:라인 | 문자열 |
|---|---|---|
| `.html()` 주입 | `arms/js/adms.js:214` | `<i class="fa fa-list"></i> 목차 보기` |
| `.html()` 주입 | `arms/js/aiChat.js:1104` | `답변 생성 중...` |
| `.html()` 주입 | `arms/js/aiSupport.js:576` | `제품 목록 조회에 실패했습니다.` |
| `innerHTML` | `arms/js/analysis/cost/circularPackingChart.js:32` | `<p>데이터가 없습니다.</p>` |
| 토글 라벨 | `arms/js/analysisScope.js:602` | `줌 기능: OFF` |
| DataTables 컬럼 title | `arms/js/adms/vesion-control.js:7,17,27` | `버전` / `생성 날짜` / `작성자` |
| 메뉴 정의 테이블 | `arms/js/aiSupport.js:16,32` | `대시보드` / `제품 관리` |
| 통계 카드 title | `arms/js/aiChat.js:1764-1766` | `전체 현황` / `요구사항` / `이슈` |
| `alert()` (주석 처리) | `arms/js/jiraServer.js:476` | `설정된 이슈유형이 없거나...` |

### 6.2 병행 i18n 스킴 3종 — 표준 불일치

`data-locale` 외에 **서로 호환되지 않는 독자 스킴이 2개 더** 존재한다. 표준화 없이 방치되면 유지보수 비용이 계속 분기한다.

| 스킴 | 속성 | 사이트 | 바인더 | 지원 로케일 | 상태 |
|---|---|---:|---|---|---|
| A (표준) | `data-locale` | 110 | `common.js:2457 bindLocaleText` | ko/en/jp(예정) | 팩 결함으로 무효 |
| B | `data-lc-i18n` | 12 | `landing_calendar.js:395` | **ko/en/ja/zh** (인라인 `LANDING_I18N`, `:104`) | 동작. 단 전역 쿠키 미사용(`:14` 주석) → **헤더 언어 전환과 미연동** |
| C | `data-i18n` / `data-i18n-html` | 158 / 29 | `landing_canyon/content-container.html:1140 applyLang` (인라인) | **ko/en만** (`:939`, `:1038`) | 동작. `localStorage` 키 `cy_canyon_lang` 독자 사용 → 전역 전환과 미연동 |

- 스킴 B는 `zh`(중국어)까지 지원하는데 전역 `allowedLocale`에는 `zh`가 없다 — 전역 표준보다 앞서 나간 지역 구현.
- 스킴 C는 페이지 내 인라인 사전 방식이라 번역 자산이 HTML에 매몰되어 있다. `jp` 확장 시 누락 위험이 가장 높다.
- §3 집계표에서 landing_calendar(16 라벨)·landing_canyon(211 라벨)의 커버리지를 0 %로 표기한 것은 **축 ①(`data-locale`) 기준**이다. 실제로는 자체 스킴으로 부분 동작하므로, 표준 통합 시 **재작업 대상이지 신규 번역 대상은 아니다**.

---

## 7. 우선순위 권고

전건 번역(9,643 + 1,833건)은 비현실적이다. **결함 수정 → 공통 영역 → 업무 화면** 순의 단계 전략을 권고한다.

### P0 — 즉시 (코드 1~3줄, 효과 즉시)

기존 투자분(태깅 110건 + 팩 43개 값)이 **현재 0 % 동작**하는 원인. 번역 작업 없이 복구된다.

| # | 조치 | 위치 | 근거 |
|---|---|---|---|
| 1 | `ko.json` trailing comma 제거 | `arms/locales/ko.json:26` | JSON 파싱 실패 → ko 폴백 전량 무효 |
| 2 | `ja`/`jp` 식별자 통일 (`jp.json`→`ja.json` 개명 **또는** `allowedLocale` 수정) | `arms/js/common.js:2417` vs `arms/locales/jp.json` | 404로 일본어 폴백 불가 |
| 3 | `reportWeekly` 빈 span에 원문 폴백 텍스트 삽입 | `arms/html/reportWeekly/content-container.html:494` | 현재 버튼 라벨 공백 렌더 |
| 4 | CI에 locale JSON 스키마/파싱 검증 추가 | (신설) | #1 재발 방지 |

### P1 — 단기 (기존 태깅 정상화)

| # | 조치 | 규모 |
|---|---|---:|
| 5 | 미정의 26키를 ko/en 팩에 추가 (`menu-nav.*` 16 · `landing.menu.*` 8 · 기타 2) | 26키 × 2언어 |
| 6 | `nav.requirement.g`/`k` en 값 추가, `nav.alm.m`·`nav.requirement.a`·`e` 양쪽 추가 | 5키 |
| 7 | `nav.language.*` 3키 추가 (언어 전환 UI 자체 번역) | 3키 |
| 8 | orphan 키 `nav.analysis.g` 정리 또는 태깅 연결 | 1키 |

P0+P1 완료 시 내비게이션·사이드바 전 영역이 ko/en에서 정상 동작한다. **누적 비용 54키 이하**로 사용자 체감이 가장 큰 공통 골격이 해소된다.

### P2 — 중기 (공통 컴포넌트 태깅 확장)

| # | 조치 | 대상 |
|---|---|---|
| 9 | `template/` 잔여 404 라벨 태깅 | `arms/html/template/**` 9파일 |
| 10 | 공통 버튼·검증 메시지·테이블 헤더를 `common.*` 네임스페이스로 통합 | 반복 라벨 우선 |
| 11 | JS용 조회 함수 `t(key)` 신설 + `currentLanguagePack` 실사용 연결 | `common.js:19,2439` |
| 12 | 스킴 B·C를 표준 `data-locale`로 흡수 (번역 자산은 재사용) | 187 사이트 |

### P3 — 장기 (업무 화면 본문)

라벨 수 기준 상위 화면부터 단계 투입. **내부 업무 화면**(reqGantt 294 · reqAdd 243 · analysis* 1,157 · detail_dashboard 187 · kpi 186 · jiraServer 184)을 **랜딩 페이지**(landing_* 약 4,000건, 마케팅 콘텐츠)보다 먼저 처리할 것을 권고한다. 랜딩은 분량이 크고 문안 변경이 잦아 ROI가 낮다.

---

## 8. Issues / Caveats

1. **이중 소스 — 정적 조사의 한계 (중요)**: 1차 언어팩은 Global-Config API(`/auth-anon/yml/language-config/packs/language/{locale}`, `common.js:2433`)이며 `arms/locales/*.json`은 **폴백**이다. API가 반환하는 키 집합은 런타임 값이라 정적 분석으로 확인 불가하다. **본 리포트의 §4 커버리지는 폴백 파일 기준**이며, API가 정상 응답하면 실제 커버리지는 이보다 높을 수 있다. 단 §1의 결함 1·2는 폴백 경로 전용 결함이므로 **API 장애 시 무방비**라는 사실은 그대로 유효하다. 정확한 실측에는 API 응답 덤프가 필요하다 — **후속 과제로 권고**.
2. **라벨 9,643건은 정규식 추출값** — 상한 추정치로 보아야 한다. `<i class="fa">` 같은 아이콘 전용 태그의 클래스 문자열, 영문 기술용어(`OFF`, `ID`), 템플릿 플레이스홀더가 일부 혼입될 수 있다. 라틴 문자 2자 이상을 라벨로 계수했기 때문이다. **폴더 간 상대 비교와 우선순위 판단에는 충분하나, 번역 발주 물량 산정 시에는 육안 검수가 필요하다.** 한국어 포함 라벨 5,693건 / 라틴 3,950건으로 분리 집계했다.
3. **커버리지 1.14 %는 "사이트 수" 기준**: 분자 110은 `data-locale` **속성 출현 수**, 분모 9,643은 **추출 라벨 수**로 산출 단위가 완전히 동일하지 않다. 한 요소가 두 축(텍스트+placeholder)에 걸릴 수 있어 미세 오차가 있다. 다만 오차 범위가 결론(98.9 % 미적용)을 바꾸지 않는다.
4. **`landing_calendar`·`landing_canyon`의 0 % 표기는 축 ① 기준**이다. 자체 스킴으로 부분 동작하므로 실제 사용자 체감은 0 %가 아니다. §6.2에 분리 기술했다.
5. **`.min.js` 제외**: JS 집계에서 압축 파일을 제외했다. 서드파티 라이브러리 내장 문자열은 감사 범위 밖으로 판단했다.
6. **`ko.json` 수리 후 가정치**: ko 정의 키 22개는 trailing comma를 제거해 파싱한 결과다. **현재 런타임 실효값은 0개**다. 두 수치를 혼동하지 말 것.
7. **미확인 사항**: `arms/index.html`·`detail.html`·`template.html`·`test.html`(`arms/` 직속)은 `arms/html/**` 범위 밖이라 조사하지 않았다. 태스크 정의 범위(164개)를 따랐다.
8. **재현 스크립트**: `artifacts/_audit.py`(라벨 추출·폴더 집계), `artifacts/_keys.py`(키↔팩 대조). 실행 시 CWD를 repo 루트로 두고 `python _audit.py arms/html` 형식으로 호출한다. 상세 결과는 `artifacts/_audit_detail.json`.

---

## Verification Checklist

- [x] **output이 brief의 output_format과 일치** — `artifacts/i18n-label-audit-report.md`에 Markdown 8섹션(①요약 ②판정기준 ③폴더별집계 ④언어별커버리지 ⑤대표사례 ⑥JS문자열 ⑦우선순위 ⑧Issues/Caveats) 직접 작성
- [x] **참조한 파일 경로가 실제 존재** — 인용 경로·라인 전부 `grep -n`으로 실측 확인(`common.js:2417/2457/2462`, `ko.json:26`, `page-navigation.html:128/255/361`, `page-header.html:48/63/78`, `mapping/content-container.html:7`, `reportWeekly/content-container.html:494`, `landing_canyon/content-container.html:1140`, `landing_calendar.js:395`). 추정 기재 없음
- [x] **task.md의 constraints 충족** — target_repo 읽기만 수행. 산출물은 `tasks/arms-i18n-label-audit/artifacts/` 내부(`write_scope: tasks-only`). 라벨·언어팩 키 변경 없음. 164개 전량 조사 명시, 두 축 분리, ko/en/jp 구분, JS 별도 섹션, 집계+대표사례+우선순위(전건 나열 아님)
- [x] **Do NOT 항목 위반 없음** — target_repo 파일 수정·생성 0건, 코드 변경 diff 미생성(권고는 조치 위치만 서술), 미확인 경로·라인 추정 기재 없음
