# Log — landing_calendar 다국어(i18n) 지원 추가

<!-- append-only. 수정/삭제 금지. -->
<!-- 형식: [YYYY-MM-DD HH:MM] [TAG] 내용 -->
<!-- TAG: DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE -->

[2026-07-22 00:00] [DECISION] routing.md 참조 → claude-main(strategist, 언어팩 구현) + frontend-expert(2계층 도메인 서브에이전트, 리뷰). Producer-Reviewer 토폴로지(reviewer=frontend-expert). codex·gemini 제외(코드 소규모·이미지 없음)
[2026-07-22 00:00] [APPROVAL] claude-main 사용자 승인. purpose: 언어팩(en/ko/zh/ja) 설계·구현 (strategist)
[2026-07-22 00:00] [DECISION] frontend-expert는 2계층 도메인 서브에이전트 → workers_approved 게이트 밖. 사용자 지정으로 리뷰 역할 수행, 투명성 위해 task.md에 병기
[2026-07-22 00:00] [WORKER_CALL] claude-main brief 전달(Task tool, subagent_type=claude-main). agentId af8fad21212d91a0c. 원문 → workers/claude-main/result.md 저장
[2026-07-22 00:00] [VERIFICATION] claude-main result 검토 — output_format ✅ (①~⑤ 전부). 참조 경로 실존 확인 ✅ (landing_calendar.js:8/136/143/94/44, locales-all.global.js, common.js getCookie/setCookie). 핵심 결정 사실검증 ✅ (common.js:2408 allowedLocale=["ko","ja","en"] → zh 미지원 확인, 서버팩 기반 확인 → 페이지-로컬 사전 결정 타당). constraints ✅, Do NOT 위반 없음(파일 직접 안 씀, buttonText 제거는 언어연동 필수). 판정: 수락
[2026-07-22 00:00] [WORKER_CALL] frontend-expert 리뷰(2계층 도메인 서브에이전트, Task tool). agentId aa7dc3a28ef63fb0b. 원문 → workers/frontend-expert/result.md 저장
[2026-07-22 00:00] [VERIFICATION] frontend-expert 리뷰 검증 — 판정: 조건부 승인. 🔴필수 2건 Orchestrator 독립 검증 완료: [필수-1] common.js:664 loadPluginGroupsParallelAndSequential→:669 로드_완료_이후_실행_함수→:509 loadLocale→:2449 bindLocaleText querySelectorAll("[data-locale]") 전역 순회 확인, landing_calendar.js:100이 동일 로더 호출 → 이중 바인딩 충돌 사실 ✅. [필수-2] dist/locales-all.global.js 부재(Glob no files), packages/core/에만 존재 → dist 경로 사용 시 404 사실 ✅. [권장-1] arms/locales에 en/jp/ko.json만·ja 없음 확인 ✅. 리뷰 정확도 높음
[2026-07-22 00:00] [DECISION] frontend-expert 수정 요청 1건 → claude-main에 1회 반영 요청 예정(필수-1 data-locale 스코프 분리, 필수-2 locales-all 경로·순서, 권장-2 셀렉터 격리). 흐름상 claude-main 재호출(수정 반영)은 승인된 워커의 검증 실패 후 재호출에 해당
[2026-07-22 00:00] [WORKER_CALL] claude-main 재호출(SendMessage, 동일 세션 af8fad21212d91a0c 컨텍스트 유지). 수정 요청: 필수-1(data-locale→전용 속성/클래스 스코프), 필수-2(locales-all 경로 packages/core/ 명시·순차), 권장-2(셀렉터 changeLocale 미호출). 백그라운드 진행 중
[2026-07-22 00:00] [VERIFICATION] claude-main v2 결과 검증 — 3건 모두 반영. 추가발견: 공통 쿠키 locale에 zh 저장 시 loadLocale→changeLocale(allowlist ko/ja/en)이 다음 로드에서 zh→ko 정규화·덮어씀. Orchestrator 재검증: common.js:2404 changeLocale(getCookie("locale")) + :2408 allowlist=["ko","ja","en"] 확인 → 주장 사실 ✅. v2 해결책(전용 저장키 landing_calendar_lang) 타당. v2 → workers/claude-main/result.md 저장
[2026-07-22 00:00] [DECISION] v2를 실제 파일에 반영(Orchestrator 직접 편집 — 워커는 텍스트 반환만). content-container.html: 셀렉터 CSS·언어 셀렉터 블록·data-lc-i18n 6곳. landing_calendar.js: 사전·헬퍼·pluginGroups locales-all 순차·locale 매핑·buttonText 제거·execDocReady 훅
[2026-07-22 00:00] [VERIFICATION] 반영 후 검증 — landingUserLocale orphan 없음(전량 landingUserLang 치환) ✅, data-locale 잔존 없음(주석 설명 1곳만) ✅, locales-all.global.js·index.global.js 파일 실존(디스크 확인) ✅
[2026-07-22 00:00] [COMPLETE] landing_calendar i18n(en/ko/zh/ja) 반영 완료. Producer-Reviewer 흐름 1사이클(claude-main→frontend-expert→claude-main) 종료. 커밋은 사용자 몫
[2026-07-22 00:00] [DECISION] 브라우저 스모크 테스트: 페이지가 grunt server(port 80)+외부 백엔드(313.co.kr) 프록시·초기화 시 /auth-anon 동기 AJAX 의존 + 세션에 브라우저 자동화 도구 없음 → 사용자 선택으로 정적 검증 대체
[2026-07-22 00:00] [VERIFICATION] 정적 스모크 PASS(node vm 하니스, scratchpad/i18n-smoke.js). 실제 landing_calendar.js·content-container.html 로드해 검증: ①HTML data-lc-i18n 6키가 4개 언어 사전에 모두 존재 ②셀렉터 option=지원언어 정확히 일치 ③bindLandingText가 언어별 정확한 텍스트 주입 ④LANDING_FC_LOCALE 매핑(en/ko/zh-cn/ja) ⑤event.* 7키×4언어 + ko/en 번역 상이 ⑥쿠키 격리(landing_calendar_lang 우선, 전역 locale=zh 무시, zh-CN→zh 정규화, 미지원→ko). 미검증: 실제 브라우저 렌더링·FullCalendar 로케일 실동작(백엔드 필요)
