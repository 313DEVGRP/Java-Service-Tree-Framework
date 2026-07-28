# Context — arms/html 언어팩 미적용 라벨 감사

## 현재 상태

task.md·워커 승인 완료. 사전 정찰로 메커니즘·규모 확인. claude-main 호출 단계.

## 핵심 정보

- 대상: `C:/DEV/sourcecode/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web` (read-only), `arms/html/**` html 164개
- 메커니즘 (`arms/js/common.js`):
  - `setLocale()` → Global-Config API, 실패 시 `arms/locales/{locale}.json` 폴백 → `flattenObject()` → `bindLocaleText()`
  - `bindLocaleText()`는 `querySelectorAll("[data-locale]")`만 순회. 키 없으면 `console.warn`만, 원문 유지
  - → **`data-locale` 없는 라벨 = 미적용**이 1차 판정 기준
  - placeholder는 `placeholder` 속성, HTML 포함 문자열은 sanitize 후 `innerHTML`
- 언어팩 `arms/locales/{ko,en,jp}.json` — **jp.json 0바이트**
- `data-locale` 보유 html 6개뿐: `template/page-navigation.html`(47) · `template/landing-navigation.html`(32) · `template/page-sidebar.html`(26) · `template/page-header.html`(3) · `mapping/content-container.html`(1) · `reportWeekly/content-container.html`(1)
- 미적용이 압도적 → 집계 + 대표 사례 방식 (사용자 결정)

## 미해결 이슈

- Global-Config API 키 집합은 런타임 값 → 정적 조사 불가. locales json 기준 판정 + caveat
- jp 부재를 "미적용" vs "키 누락" → 두 축 분리 표기

## 참조 자료

- tasks/요구사항_TASK_전환_Sample.md (REQ-F-001 원문)
