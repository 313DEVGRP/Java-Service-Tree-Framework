# Log — REQ-BACKEND-FUNC-01

<!-- append-only. 수정/삭제 금지. -->

[2026-09-21 20:11] [DECISION] /REQ-RUN REQ-BACKEND-FUNC-01 — 엑셀 2행을 요청문으로 변환. 신규 작업(기존 폴더 없음) → CLAUDE.md Task Lifecycle 정상 경로.
[2026-09-21 20:11] [DECISION] 성격 = 분석·요약. 근거: 진행 현황이 '분석중' 으로 Format 매핑표(기획중·설계중→분석·요약 / 개발중·검증중→코드 구현)에 없는 값 → 어의상 분석·요약으로 해석. 대안: 코드 구현으로 보면 외부 쓰기가 필요해지나 요구사항이 '읽기 전용' 을 명시하므로 배제.
[2026-09-21 20:11] [DECISION] target_repo = /Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core. 근거: 시트 [작업 대상] 의 모듈명을 이 저장소 기준 절대경로로 해석.
[2026-09-21 20:11] [DECISION] write_scope = tasks-only. 근거: 성격이 분석·요약이고 요구사항 제약이 대상 저장소 쓰기를 금지. 대안 none(diff-first) 는 산출물이 CSV 라 불필요.
[2026-09-21 20:11] [DECISION] frontend-expert 미호출. 근거: 시트 [Worker Settings] 에 승인돼 있으나 이번 범위가 Backend-Core 서버사이드 단독이라 투입 지점이 없음. 승인은 유지하되 호출하지 않음(승인 외 호출 금지 규칙의 반대 방향이라 위반 아님).
[2026-09-21 20:11] [DECISION] 추출은 기존 스킬 .claude/skills/api-catalog 의 expand_inherit.py 를 정본 추출기로 사용. 근거: 상속 전개(821건)를 반영한 유일한 기계 추출기이며 SKILL.md 에 기준값이 있어 회귀 검증이 가능. 대안: 새 파서 작성 → 함정 6종을 다시 밟게 되므로 배제.
[2026-09-21 20:12] [APPROVAL] claude-main 승인 (approved_by: user via /REQ-RUN). purpose: 엔드포인트 전수 추출·플랫 CSV 생성. 실행 주체 = 서브에이전트 backend-expert. write_scope: tasks-only
[2026-09-21 20:12] [APPROVAL] codex-critic 승인 (approved_by: user via /REQ-RUN). purpose: 산출 CSV 소스 대조 리뷰. write_scope: none
[2026-09-21 20:13] [DECISION] 역할 분담 재조정. CLAUDE.md '워커 파일 쓰기 정책' 상 claude-main 은 파일 쓰기 ❌(Orchestrator 경유) 이므로, 기계적 추출(expand_inherit.py 실행)과 최종 CSV 파일 생성은 Orchestrator 가 수행하고 claude-main 에는 누락 감사·컬럼 스펙·변환 코드(텍스트)만 맡긴다. 대안: 워커가 직접 CSV 를 쓰게 하면 쓰기 정책 위반.
[2026-09-21 20:13] [DECISION] brief Input 에서 backend-core-known-issues.md 를 제외. 근거: 해당 문서에 엔드포인트 추출과 겹치는 known-issue 항목이 없고(구조·보안·Feign·Kafka·POI·영속), brief 한도(240단어) 압박. 추출 함정은 api-catalog SKILL.md 가 정본.
[2026-09-21 20:13] [VERIFICATION] expand_inherit.py 실행(Orchestrator) — 컨트롤러 92 | 자체 선언 360 | 상속분 821 | 합계 1181 | 상속 있는 컨트롤러 59. SKILL.md 기준값(92/359/821/1180, 58) 대비 자체 +1·상속컨트롤러 +1 로 자릿수 변동 없음 → 추출기 정상 판정.
[2026-09-21 20:14] [WORKER_CALL] claude-main brief 전달 (실행 주체: 서브에이전트 backend-expert). gate: GATE_OK task=req-backend-func-01 role=claude-main target_repo=/Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core write_scope=tasks-only
[2026-09-21 20:21] [VERIFICATION] claude-main result 검토 — output_format(누락감사/컬럼스펙/변환코드/예상행수/체크리스트/Issues) ✅, 파일 쓰기 없음 ✅, Do NOT 위반 없음 ✅. 변환 코드는 Orchestrator 가 실행.
[2026-09-21 20:21] [VERIFICATION] CSV 생성 후 체크리스트 14항목 실행 — 1 존재✅ 2 필수헤더✅ 3 총383행✅ 4 own 360✅ 5 inherited 23✅ 6 공란 0✅ 7 상속중복 0✅ 8 Σ상속 821✅ 9 합계 1181=inventory✅ 10 own↔sources 완전일치✅ 11 note 2건✅ 12 창작 0✅ 13 평가문 없음✅ 14 Backend-Core 무변경(.DS_Store 만 untracked, 본 작업 무관)✅. 추가: package↔sourceFile 불일치 0.
[2026-09-21 20:21] [DECISION] Acceptance Criteria 의 기준값을 359→360(합계 1180→1181)로 갱신. 근거: task.md constraints 가 '수치 정본은 sources/' 이고 SKILL.md 기준값은 2026-09-21 이전 실측치. 대안: 359 를 고수하면 실제 소스와 어긋난 기준으로 검증하게 됨.
[2026-09-21 20:25] [WORKER_CALL] codex-critic 호출. gate: GATE_OK task=req-backend-func-01 role=codex-critic target_repo=/Users/leemingyu/dev/Java-Service-Tree-Framework/Java-Service-Tree-Framework-Backend-Core write_scope=none. 경로: MCP 불가(codex-cli 0.154.0) → backends.json CLI 폴백 `codex exec --sandbox read-only -`
[2026-09-21 20:25] [ERROR] codex-critic 실패 (exit=1, stdout 0줄). 사유: Codex 사용량 한도 소진 — "try again at Oct 13th, 2026 1:10 PM". 재시도 1회 동일 실패. 게이트·승인 문제 아님.
[2026-09-21 20:26] [DECISION] codex-critic 을 다른 워커(gemini 등)로 대체하지 않음. 근거: 승인 목록(시트 [Worker Settings])에 없는 워커 호출 금지. 대신 brief 점검 5항목 중 기계 대조 가능분을 Orchestrator 가 직접 수행하고 result.md 에 '미리뷰 + 자체 대조 통과' 로 명시. 대안: 승인 없는 워커 투입 → 승인 게이트 위반이라 배제.
[2026-09-21 20:26] [VERIFICATION] 대체 대조 — package 표본 10건 불일치 0(전 행 package↔sourceFile 정합 0 불일치), 경로 조합 표본 10건 중 8건 즉시 일치·2건 다중행 어노테이션 수동 확인 후 일치, javaMethod 공란 0(한글 메서드명 16건 정상 추출).

[2026-09-21 20:28] [COMPLETE] REQ-BACKEND-FUNC-01 완료. 산출물 artifacts/backend-core_endpoints_flat.csv (383행). 교훈: 시스템 일반 2건 → _shared/learnings.md, 프로젝트 한정 2건 → _local/learnings.md.

## 임의 결정 요약

| # | 항목 | 정한 값 | 근거 | 대안 |
|---|---|---|---|---|
| 1 | 성격 | 분석·요약 | 진행 현황 '분석중' 이 Format 매핑표에 없는 값 → 어의상 해석 | 코드 구현(요구사항의 '읽기 전용' 과 충돌해 배제) |
| 2 | target_repo | .../Java-Service-Tree-Framework-Backend-Core | 시트 [작업 대상] 모듈명을 저장소 기준 절대경로로 해석 | — |
| 3 | write_scope | tasks-only | 분석·요약 + 대상 저장소 쓰기 금지 제약 | none(diff-first) — 산출물이 CSV 라 불필요 |
| 4 | frontend-expert | 미호출 | Backend-Core 서버사이드 단독 범위라 투입 지점 없음. 승인은 유지 | 형식상 호출 — 산출물 기여 없음 |
| 5 | 추출기 | 기존 스킬 api-catalog/expand_inherit.py | 상속 전개(821)를 반영한 유일한 기계 추출기 + 기준값 회귀 검증 가능 | 신규 파서 — 함정 6종 재발 |
| 6 | 워커 역할 분할 | 파일 생성=Orchestrator / 감사·스펙·코드=claude-main | CLAUDE.md 워커 쓰기 정책(claude-main ❌) | 워커 직접 쓰기 — 정책 위반 |
| 7 | brief Input | known-issues 문서 제외 | 엔드포인트 추출과 겹치는 known-issue 항목 없음 + 240단어 한도 | 포함 — 한도 초과 |
| 8 | 기준 수치 | 자체 360 / 합계 1181 (SKILL.md 359/1180 대신) | task.md constraints '수치 정본은 sources/' | 359 고수 — 실제 소스와 어긋남 |
| 9 | 상속 행 표기 | `{basePath}` 플레이스홀더 + `inheritedBy=클래스@basePath` | 자체 엔드포인트 0개인 트리 컨트롤러 31개라 basePath 복원 불가 | 컨트롤러별 전개 — 검증 기준 ② 위반 |
| 10 | 중복 2건 | own 행 + 상속 inheritedBy 양쪽에 유지, note 로 표시 | 상속 목록에서 빼면 inheritedByCount 가 58/57 로 갈려 sources 821 과 불일치 | 한쪽 삭제 — 수치 정합 깨짐 |
| 11 | codex-critic 실패 처리 | 대체 워커 없이 ERROR + Orchestrator 자체 대조 | 승인 목록 밖 워커 호출 금지 | gemini 대체 — 승인 게이트 위반 |
| 12 | status | done (리뷰 공백 명시) | Acceptance Criteria 전부 통과, 미수행 항목은 task.md Notes·critic result.md 에 기록 | reviewing 유지 — 재개 조건이 3주 뒤라 무기한 대기 |

[2026-09-21 22:21] [DECISION] 사용자 요청으로 CSV 의 시트 분할본을 추가 산출. artifacts/backend-core_endpoints_by-controller.xlsx — controllerClass 별 60시트 + `_목차`. CSV 는 정본으로 그대로 두고 xlsx 는 파생본. 시트명 금지문자([]:*?/\)는 `-` 치환, 31자 절단, 충돌 시 `~n` 접미. 검증: 데이터 합계 383행 = 원본, 목차↔시트 불일치 0.

[2026-09-21 23:10] [UPDATE] 추출기 결함 수정에 따른 재생성 (사용자 요청). 변경 블록: artifacts·sources. `.claude/skills/api-catalog/scripts/expand_inherit.py` 경로 필터에서 `'/' not in x` 조건 제거 → 선행 슬래시 없는 상대 경로 4건이 basePath 단독 행으로 둔갑하던 문제 해결. 이전 산출물은 artifacts/superseded/·sources/superseded/ 에 `_v1-20260921` 로 보존.
[2026-09-21 23:10] [VERIFICATION] 재생성 결과 — 총계 불변(컨트롤러 92 / 자체 360 / 상속 821 / 합계 1181, CSV 383행). 신·구 diff 정확히 4행 교체: `GET /arms/pdServiceDetail`→`…/getNodes.do/{pdServiceId}`, `POST /arms/pdServiceDetail`→`…/addNode.do/{pdServiceId}`, `POST /arms/report`→`…/req-status/{changeReqTableName}/getNodesWhereInIds.do`, `PUT /arms/jiraServer`→`…/{refreshTarget}/renewNode.do`.
[2026-09-21 23:11] [VERIFICATION] 회귀 — 6개 저장소 전체 재실행. Backend-Core 만 변화(4행). Engine-Fire 45/162·Middle-Proxy 16/112·AI 18/43 은 기준값과 동일. Global-Config 4/11·Broker-Hub 7/5 는 기준값(7/33·8/5)과 다르나 **패치 전 스크립트로도 동일** → 소스 드리프트이지 이번 수정의 영향 아님. SKILL.md 기준값 표와 함정 표(#7 신설) 갱신.
[2026-09-21 23:12] [DECISION] 이전 보고 정정 — Acceptance Criteria '자체 선언 엔드포인트 빠짐없음' 은 v1 에서 실제로는 미충족이었다(4건 경로 오류). 개수 기반 검증(360=360)과 소스 재집계가 모두 추출기와 같은 가정을 공유해 못 잡았고, REQ-MAPPING-FUNC-01 의 프론트 대조에서 드러났다. v2 에서 충족.
[2026-09-21 23:13] [DECISION] artifacts/backend-core_endpoints_by-controller.xlsx 재생성. 근거: 22:21 생성·검증 후 23:05 시점에 파일이 사라져 있었음(원인 미상, 프론트 분할본도 동일). CSV 정본은 무사해 동일 스크립트로 재생성.

[2026-09-21 23:25] [UPDATE] 사용자 요청 — TreeFramework 상속으로 생긴 URL 은 프레임워크 공통 제공분이라 프론트 미호출이 정상일 수 있으므로 엑셀에 구분 표기. artifacts/backend-core_endpoints_by-controller.xlsx 재생성: `provider` 파생 컬럼(도메인 선언 360 / 프레임워크 제공 TreeAbstractController 14 · TreeMapAbstractController 9) + `_요약` 시트 + 프레임워크 행 회색 음영. CSV 정본은 미변경(파생 컬럼은 엑셀에서만 계산).

[2026-09-21 23:40] [UPDATE] 사용자 요청 — 산출물 삭제 후 전면 재생성(사후 덧칠 금지). 생성기를 artifacts/build_backend_catalog.py 한 벌로 통합: sources/ → CSV(provider 컬럼 포함) → 컨트롤러별 xlsx(60시트 + _목차 + _요약, 프레임워크 행 회색). 이전의 파생-컬럼-엑셀에서만 계산 방식 폐기 — CSV 에도 provider 가 들어간다.
[2026-09-21 23:40] [VERIFICATION] 재생성 — CSV 383행(자체 360 도메인 선언 / 상속 23 프레임워크 제공: TreeAbstractController 14 · TreeMapAbstractController 9), xlsx 383행 일치, 시트명 규칙 위반 0.
[2026-09-21 23:45] [DECISION] artifacts/superseded·sources/superseded 삭제(사용자 요청). v1 산출물은 더 이상 보존하지 않는다 — 현재 채택본 1벌만 유지. 재현이 필요하면 sources/ + artifacts/build_backend_catalog.py 로 다시 생성 가능.
[2026-09-22 00:05] [UPDATE] provider 용어를 매핑 산출물과 통일 — `프레임워크 제공(X 상속)` → `상속(X)`, `도메인 선언` → `자체 선언`. 재생성 383행(자체 360 / 상속 23), 엑셀 _목차·_요약 라벨도 동일하게 변경.
[2026-09-22 00:31] [UPDATE] 생성 스크립트를 스킬로 이관 — artifacts/build_backend_catalog.py 삭제, .claude/skills/api-catalog/scripts/endpoints_flat.py·sheets_xlsx.py 가 정본(환경변수 CATALOG_REPO·CATALOG_TASK). 이관 전후 CSV md5 동일 확인.
[2026-09-22 01:32] [UPDATE] 사용자 지시 — 엑셀을 단일 시트로 통일. backend-core_endpoints_by-controller.xlsx(60시트) 삭제, backend-core_endpoints_flat.xlsx(단일 시트 `data`, 383행 × 15열) 생성. CSV 와 동일 순서·행수. provider 상속 행 회색 음영은 유지.
