# result.md — codex-critic / REQ-FRONTEND-FUNC-01

## 상태: 미수행 (ERROR)

호출 2회(최초 + 재시도 1회) 모두 실패. 산출물 없음. REQ-BACKEND-FUNC-01 과 동일 사유.

| 항목 | 값 |
|---|---|
| 호출 경로 | MCP 불가(codex-cli 0.154.0) → `backends.json` CLI 폴백 `codex exec --sandbox read-only -` |
| 결과 | `exit=1`, stdout 0줄 |
| 에러 | `ERROR: You've hit your usage limit. … try again at Oct 13th, 2026 1:10 PM.` |
| 게이트 | `GATE_OK task=req-frontend-func-01 role=codex-critic write_scope=none` (승인 문제 아님) |

## 대체 조치 (Orchestrator 수행 — 워커 호출 아님)

| brief 점검 항목 | 대체 수행 | 결과 |
|---|---|---|
| 1 말미 `/` | CSV 전 행 검사 | 0건 |
| 2 호출 지점 누락 | 소스에서 프리미티브 5종을 독립 재집계해 워커 표와 대조 | `$.ajax` 404 · `$.get` 9 · `$.post` 1 · `$.getJSON` 2 · `fetch` 8 — 워커 실측치와 전건 일치 |
| 3 필수 3컬럼 공란 | CSV 전 행 검사 | 0건 |
| 4 URL 복원 표본 | 워커가 제시한 5건을 소스 원문과 대조 | 5건 모두 일치 (아래) |
| 5 메뉴 매핑 | `page-navigation.html`·`page-sidebar.html` 존재·링크 수 확인, 라벨 63종 | 일치 |
| 6 arms·backoffice 포함 | area 분포 | arms 418 / backoffice 122 |

표본 5건 대조 근거:

| CSV | 소스 |
|---|---|
| `POST /auth-user/api/arms/pdServiceDetail/deleteNode.do/{selectedDetailId}` | `pdService.js:1086` `url: "…deleteNode.do/" + selectedDetailId`, `type:"post"` |
| `GET /auth-user/api/arms/reqAddStatePure/T_ARMS_REQADD_{selectId}/monthlyProgressRate` | `reqGantt.js:400` `endPointUrl = "/T_ARMS_REQADD_"+selectId+"/monthlyProgressRate"` + `:406` base 연결 |
| `GET /auth-user/api/kafka/REQADD-DLT/list` | `kafkaAdmin.js:4` `KAFKA_ADMIN_BASE_URL="/auth-user/api/kafka/"` + `:6` `DLT_TOPIC="REQADD-DLT"` + `:223` |
| `POST /auth-user/search/engine/search/{almIssue\|log\|wiki}` 3행 + 일반형 1행 | `searchEngine.js:189` `"…/search/" + searchSection`, 호출부 값 almIssue·log·wiki |
| jsTreeBuild 경유 행 | `note` 에 `common.js:<line> 경유` 기록 확인 |

## Orchestrator 가 추가로 발견한 사항 (워커 result 에 없음)

- **조건부 쿼리스트링 `+=` 변형이 부분적으로만 전개된다.** `url/endPointUrl += "?…"` 패턴이 13곳 있는데
  CSV 의 쿼리스트링 포함 행은 73행, `reqGantt.js` 는 21행 중 4행만 `?` 를 갖는다.
  예: `reqGantt.js:403` 의 `?c_req_pdservice_versionset_link={selecteVersionId}` 변형은 CSV 에 없다.
  경로 자체는 맞고 검증 기준(말미 `/`)도 위반이 아니므로 **행을 고치지 않고 한계로 기록**한다.

## 미대체 (제3자 시각이 필요한 부분)

- 범위 판정의 타당성 — 프리미티브 밖 config `url:` 34건 포함, `$.getScript` 계열 18건 제외, 클라이언트사이드 DataTable 18건 제외
- 디스패처 경유 행을 호출부 라인에 두는 선택(중복 방지 vs 원지점 추적성)
- 수작업 dict 17개 지점의 근거 재현

## 재개 방법

```bash
bash _shared/adapters/gate.sh tasks/req-frontend-func-01/workers/codex-critic/brief.md
cat tasks/req-frontend-func-01/workers/codex-critic/brief.md | codex exec --sandbox read-only -
```
