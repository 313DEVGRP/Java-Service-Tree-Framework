# Log — REQ-FRONTEND-FUNC-01

<!-- append-only. 수정/삭제 금지. -->

[2026-09-21 20:40] [DECISION] /REQ-RUN REQ-FRONTEND-FUNC-01 — 엑셀 3행을 요청문으로 변환. 신규 작업(기존 폴더 없음) → CLAUDE.md Task Lifecycle 정상 경로.
[2026-09-21 20:40] [DECISION] 성격 = 분석·요약. 근거: 진행 현황 '분석중' + 요구사항이 읽기 전용 명시. 대안 코드 구현은 제약과 충돌.
[2026-09-21 20:40] [DECISION] target_repo = .../Java-Service-Tree-Framework-Frontend-Web. 근거: 시트 [작업 대상] 이 같은 저장소의 두 하위 경로(arms/js/, backoffice/js/)를 가리키므로 저장소 루트를 target_repo 로 두고 두 경로를 범위로 명시.
[2026-09-21 20:40] [DECISION] write_scope = tasks-only. 근거: 분석·요약 + 저장소 쓰기 금지 제약.
[2026-09-21 20:40] [DECISION] 완료 조건 보강. 시트 [검증 기준] 이 '/로 끝나는 api 금지' 1개뿐이라 [상세 기능 요구사항]에서 ②(menuname·jsfilename·apiurl 채움) ③(arms·backoffice 양쪽 포함)를 유도해 추가. 근거: 단일 기준만으로는 '빈 CSV 도 통과' 가 되어 수락 판정이 불가능.
[2026-09-21 20:40] [DECISION] 역할 분담 = REQ-BACKEND-FUNC-01 과 동일. claude-main 은 파일 쓰기 ❌ 이므로 추출 스펙·복원 결과·변환 코드만 텍스트로 받고, 실행·파일 기록은 Orchestrator.
[2026-09-21 20:41] [APPROVAL] claude-main 승인 (approved_by: user via /REQ-RUN). purpose: js API 전수 추출·URL 복원·메뉴 매핑. 실행 주체 = 서브에이전트 frontend-expert. write_scope: tasks-only
[2026-09-21 20:41] [APPROVAL] codex-critic 승인 (approved_by: user via /REQ-RUN). purpose: 산출 CSV 소스 대조 리뷰. write_scope: none
[2026-09-21 20:43] [WORKER_CALL] claude-main brief 전달 (실행 주체: 서브에이전트 frontend-expert). gate: GATE_OK task=req-frontend-func-01 role=claude-main target_repo=/Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Frontend-Web write_scope=tasks-only
[2026-09-21 21:56] [VERIFICATION] claude-main result 검토 — output_format(추출범위/컬럼스펙/URL복원/메뉴매핑/변환코드/예상행수/체크리스트/Issues) ✅, 파일 쓰기 없음(스크래치패드만) ✅, Do NOT 위반 없음 ✅. 변환 코드 원본을 workers/claude-main/extract_api_calls.py 로 보존(926줄), result.md §6 은 경로 참조.
[2026-09-21 21:57] [VERIFICATION] CSV 생성 후 체크리스트 실행 — 스크립트 exit 0, stdout `rows=540 files=169 trailing-slash=0 blank=0 unresolved=4` 워커 드라이런과 일치. 헤더 ✅ / 말미 `/` 0 ✅ / 필수3 공란 0 ✅ / area arms 418·backoffice 122 ✅ / UNRESOLVED 4건 전부 note 보유 ✅ / jsfile 경로 전건 실존 ✅ / Frontend-Web 무변경 ✅. 부가: distinct apiurl 382, 파일 81/169, 메뉴 라벨 63종.
[2026-09-21 21:58] [WORKER_CALL] codex-critic 호출. gate: GATE_OK task=req-frontend-func-01 role=codex-critic write_scope=none. 경로: CLI 폴백 `codex exec --sandbox read-only -`
[2026-09-21 21:58] [ERROR] codex-critic 실패 (exit=1, stdout 0줄). 사유: Codex 사용량 한도 소진 — "try again at Oct 13th, 2026 1:10 PM". 재시도 1회 동일 실패.
[2026-09-21 21:59] [DECISION] REQ-BACKEND-FUNC-01 과 동일하게 대체 워커 투입 없이 Orchestrator 자체 대조로 진행. 근거: 승인 목록 밖 워커 호출 금지.
[2026-09-21 21:59] [VERIFICATION] 대체 대조 — 프리미티브 5종 독립 재집계($.ajax 404·$.get 9·$.post 1·$.getJSON 2·fetch 8)가 워커 표와 전건 일치. URL 복원 표본 5건 소스 원문 대조 전건 일치.
[2026-09-21 21:59] [DECISION] 발견된 한계(조건부 쿼리스트링 `+=` 변형 부분 전개 — 13곳 중 일부 누락, 예 reqGantt.js:403)를 수정하지 않고 기록만 함. 근거: 경로는 정확하고 검증 기준(말미 `/`) 위반이 아니며, 쿼리 변형 전수 전개는 요구사항 범위 밖. 대안: 재호출해 보정 → 범위 확대라 배제.

[2026-09-21 22:00] [COMPLETE] REQ-FRONTEND-FUNC-01 완료. 산출물 artifacts/frontend-web_api-calls_flat.csv (540행). 교훈: 프로젝트 한정 1건 → _local/learnings.md.

## 임의 결정 요약

| # | 항목 | 정한 값 | 근거 | 대안 |
|---|---|---|---|---|
| 1 | 성격 | 분석·요약 | 진행 현황 '분석중' + 읽기 전용 제약 | 코드 구현 — 제약과 충돌 |
| 2 | target_repo | .../Java-Service-Tree-Framework-Frontend-Web | [작업 대상] 두 경로가 같은 저장소 하위라 루트를 target 으로 | 경로별 분리 — 워커 2회 호출 |
| 3 | write_scope | tasks-only | 분석·요약 + 저장소 쓰기 금지 | none(diff-first) — CSV 산출이라 불필요 |
| 4 | 완료 조건 보강 | ②(필수 3컬럼) ③(arms·backoffice 양쪽) 추가 | 시트 [검증 기준]이 '말미 / 금지' 1개뿐이라 빈 CSV 도 통과 | 원문 그대로 — 수락 판정 불가 |
| 5 | 역할 분할 | 파일 생성=Orchestrator / 추출 스펙·복원·코드=claude-main | CLAUDE.md 워커 쓰기 정책 | 워커 직접 쓰기 — 정책 위반 |
| 6 | 추출 범위 확대 채택 | 프리미티브 424 + 플러그인/래퍼 config 34 = 458 지점 | 워커 근거: config 34곳을 빼면 analysis/top-menu·realms/master/users 등 실사용 엔드포인트 누락 | 프리미티브만 — 누락 발생 |
| 7 | `$.getScript` 계열 18건 제외 | 제외 | 정적 js/css 로더로 REST 아님 | 포함 — 레퍼런스 성격과 불일치 |
| 8 | 클라이언트사이드 DataTable 18건 제외 | 행 미생성 | `ajaxUrl=""` 로 네트워크 호출 없음 | 포함 — 빈 apiurl 이 되어 완료 조건 ② 위반 |
| 9 | 디스패처 경유 행 위치 | 호출부(caller) 파일:라인 | 메뉴 단위 집계 정합. 원지점은 note 에 기록 | 빌더 내부 라인 — 메뉴 매핑 불가 |
| 10 | 복원 불가 4건 표기 | `UNRESOLVED:<표현식>` + note 사유 | 공란 금지(완료 조건 ②) + 말미 `/` 아님 | 행 삭제 — 추적 불가 |
| 11 | 쿼리스트링 `+=` 부분 전개 | 한계로 기록, 미보정 | 경로 정확·기준 위반 아님. 전수 전개는 범위 밖 | 재호출 보정 — 범위 확대 |
| 12 | codex-critic 실패 처리 | ERROR + Orchestrator 자체 대조 | 승인 목록 밖 워커 호출 금지 | gemini 대체 — 승인 게이트 위반 |
| 13 | status | done (리뷰 공백 명시) | Acceptance Criteria 전부 통과 | reviewing 유지 — 3주 무기한 대기 |

[2026-09-21 22:21] [DECISION] 사용자 요청으로 CSV 의 시트 분할본을 추가 산출. artifacts/frontend-web_api-calls_by-menu.xlsx — menuname 별 63시트 + `_목차`. CSV 는 정본으로 그대로 두고 xlsx 는 파생본. 사유 라벨의 대괄호(`[공통모듈]` 등)는 시트명 금지문자라 `-공통모듈-` 로 치환됨(목차 B열에 원래 값 보존). 검증: 데이터 합계 540행 = 원본, 목차↔시트 불일치 0.

[2026-09-21 23:40] [UPDATE] 사용자 요청 — by-menu xlsx 재생성. 생성기를 artifacts/build_menu_xlsx.py 로 작업 폴더에 보존(이전에는 스크래치패드 스크립트라 재현 불가했음). CSV 정본 미변경.
[2026-09-21 23:40] [VERIFICATION] xlsx 63시트 + _목차, 540행 CSV 와 일치, 시트명 규칙 위반 0.
[2026-09-22 00:30] [UPDATE] 사용자 지시 — 프론트 호출 중 Tree CRUD 를 부르는 것도 '상속' 으로 표기. front_calls.py 에 provider 컬럼 추가(CATALOG_BE_CSV 주면 백엔드 카탈로그의 kind=inherited 경로 suffix 23종으로 자동 판별, tree_actions.py 공용 헬퍼). 재생성 540행 — 상속(TreeAbstractController) 88 / 일반 호출 452 (arms 73+345, backoffice 15+107). xlsx 63시트 + _요약(area × provider).
[2026-09-22 00:30] [DECISION] 액션 목록을 스크립트에 하드코딩하지 않고 백엔드 카탈로그에서 로드. 근거: 목록을 손으로 적으면 상속 매핑이 바뀔 때 조용히 어긋난다. 대안: 상수 배열 → SKILL.md '표를 손으로 적지 않는다' 규칙 위반.
[2026-09-22 00:31] [UPDATE] 생성 스크립트를 스킬로 이관 — artifacts/build_menu_xlsx.py·workers/claude-main/extract_api_calls.py 삭제, .claude/skills/api-catalog/scripts/front_calls.py·sheets_xlsx.py 가 정본. 이관 전후 CSV md5 동일 확인.
[2026-09-22 01:00] [UPDATE] 사용자 지시 — 메뉴명에서 추정 제거. front_calls.py 의 메뉴 해석을 ①네비 라벨 → ②html/<page>/content-header.html 의 breadcrumb·h3 → ③공통 모듈 → ④페이지 키 순으로 재작성하고 `page`·`menusource` 컬럼 추가. 재생성 540행 — 출처 분포 네비게이션 400 · content-header 109 · 공통 25 · 페이지키 6. `[메뉴미연결·…]` 대괄호 라벨과 추정 문구 0건. 메뉴명 62종.
[2026-09-22 01:00] [DECISION] 한 메뉴명이 여러 페이지를 덮는 경우(`Dashboard` 가 detail_* 6개 등) `이름 (page)` 로 구분. 근거: 그대로 두면 서로 다른 화면이 한 시트로 합쳐져 정보가 뭉개진다. 추정이 아니라 실제로 같은 헤더를 쓰는 사실이므로 이름은 보존하고 괄호만 덧붙였다. 대안: 페이지 키로 시트 분할 → 요구사항이 menu 별이라 배제.
[2026-09-22 01:32] [UPDATE] 사용자 지시 — 엑셀을 단일 시트로 통일. frontend-web_api-calls_by-menu.xlsx(62시트) 삭제, frontend-web_api-calls_flat.xlsx(단일 시트 `data`, 540행 × 11열) 생성. CSV 와 동일 순서·행수.
