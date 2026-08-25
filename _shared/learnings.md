# Shared Learnings

작업 완료 후 재사용 가능한 교훈만 추가. append-only.  
중복·일회성·작업 특화 내용은 기록하지 말 것.

## 분류 규칙 (어디에 적을지)

- **시스템 운영 자체**에 대한, 어떤 작업에든 적용되는 교훈 → **이 파일** (`_shared/learnings.md`, git 추적·공개).
- **특정 외부 프로젝트/repo에 묶인** 교훈(예: mat·hwpx 내부) → **`_local/learnings.md`** (git 추적 안 함·미배포. 없으면 새로 생성. 오케스트레이터는 명시 요청 없이는 로드하지 않음).

## 형식

```
## [YYYY-MM-DD] [작업명]
**교훈**: 한 문장. 다음 작업에 그대로 적용 가능한 형태로.
**근거**: 왜 그런지, 어떤 작업에서 발견했는지.
**worker**: [관련 worker명]
```

---

<!-- 이 아래부터 교훈 추가 -->

## [2026-05-13] [mat-mvp]
**교훈**: orchestrator-cwd가 git이 아니면 Task tool sub-agent 호출에서 worktree 격리가 실패할 수 있다. 다른 git repo를 다룰 때는 그 repo로 `cd` 후 claude를 시작하거나, worktree를 요구하지 않는 일반 에이전트로 폴백.
**근거**: claude-test(비-git) cwd에서 `subagent_type: claude` 호출 시 "Cannot create agent worktree" 에러. `general-purpose`로 재시도하니 격리 없이 성공.
**worker**: claude-main 호출 경로

## [2026-05-14] [mat-mvp]
**교훈**: `task.md`는 ` ```yaml ` 블록을 2개 갖는 게 표준 패턴(메타 + Worker Plan)이다. 어떤 키든 첫 yaml fence만 보는 파서는 깨진다 — 문서 전체의 모든 yaml block을 스캔하도록 작성할 것.
**근거**: mat의 `readPlannedWorkers`가 첫 fence 닫는 ``` 에서 return하는 바람에 `planned_workers`(두 번째 블록)를 못 봤다. codex-critic이 MAJOR로 잡고 fix iter로 수정.
**worker**: codex-critic (지적), claude-main (수정)

## [2026-05-14] [mat-mvp]
**교훈**: 같은 worker의 재호출(fix iter)은 별도 폴더 만들지 말고 같은 worker 폴더 안에서 `brief-fix.md` / `result-fix.md` 명명으로 진행. 1차 산출물·승인 기록을 보존하면서 변경 이력이 시각적으로 드러난다.
**근거**: codex-critic 리뷰 후 claude-main에 MAJOR 2건 패치 재호출 시 적용. `workers_approved`는 그대로 두고 brief/result 한 쌍을 추가하는 것만으로 충분했고 깔끔했다.
**worker**: claude-main (fix iter)

## [2026-05-14] [yt-thumbnail-multiagent]
**교훈**: MultiAgent 작업은 worktree 진입 금지. orchestration 산출물(`tasks/<task>/`)은 gitignore라 worktree에 만들어도 본체로 옮기려면 수동 복사 사족이 생긴다. tracked 시스템 파일도 단순 append/수정에 worktree+commit+merge는 과한 오버헤드.
**근거**: 배경 세션 harness가 자동으로 EnterWorktree를 강제해 task 폴더와 시스템 파일 수정 양쪽에서 `cp -R` 또는 머지 사족이 발생했다. 외부 `target_repo` 쓰기는 codex-main의 cwd로 따로 격리되므로 MultiAgent repo 자체에 워크트리는 불필요. 인터랙티브 세션에서는 EnterWorktree를 자발적으로 호출하지 말 것.
**worker**: orchestrator (세션 초기화 시 EnterWorktree 호출 안 함)

## [2026-05-14] [yt-thumbnail-spring]
**교훈**: log.md는 표준 형식 엄수 — (a) 태그는 정해진 6종(`DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE`)만 사용, (b) 타임스탬프 `[YYYY-MM-DD HH:MM]`까지 기록, (c) 작업 완료 시 마지막 줄에 `[COMPLETE]` 엔트리 필수.
**근거**: yt-thumbnail-spring log에서 `INIT/BRIEF/CALL/RESULT` 새 태그 사용, HH:MM 누락, [COMPLETE] 부재. mat 같은 도구가 표준 형식 가정하고 파싱하면 일관성 깨짐.
**worker**: orchestrator (로그 작성 규율)

## [2026-05-15] [hwpx-math-final]
**교훈**: codex MCP 호출이 비정상적으로 길어질 때(>2-3분) 첫 의심은 외부 MCP 도구 hang이지 모델·reasoning이 아니다. `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`의 event timestamp gap을 보면 어느 function_call에서 막혔는지 즉시 식별 가능.
**근거**: 표면 원인(reasoning=high, brief 길이, AGENTS preamble)으로 잘못 짚었다가 사용자 재질문 후 turn timing 분석으로 진단. 탐색·normalize는 50초, hang난 function_call→output 사이가 399초로 명확. session jsonl이 정답지.
**worker**: orchestrator (디버깅 절차)

## [2026-05-15] [hwpx-math-final]
**교훈**: `mcp__codex__codex`의 reject 응답이 codex backend 작업을 중단시키지 않는다. 사용자 거부 후에도 backend는 끝까지 실행되어 파일·부수 효과가 남을 수 있음. 거부한 호출 직후엔 대상 디렉토리 상태를 반드시 확인.
**근거**: reject된 codex MCP 호출 두 건이 backend에서 작업을 계속해 cwd에 산출 파일 생성. orchestrator는 처음에 그 파일들이 어디서 왔는지 추적 못 함. `~/.codex/sessions/` 세션 jsonl로 확인 가능.
**worker**: orchestrator (MCP reject 의미 이해)

## [2026-05-15] [manual-final-review]
**교훈**: `mcp__gemini-pro__*`(로컬 프록시 기반 gemini-pro 브리지)가 `Proxy 400 INVALID_ARGUMENT`를 내면 프롬프트 크기 문제가 아니라 모델 티어 문제일 수 있다 — 압축 재시도로 시간 쓰지 말고 폴백 순서를 `pro-high → pro-low(같은 프록시, 종종 정상) → Flash 브리지`로 단계 강등하라. 어느 경우든 model deviation을 result.md·리포트에 명시한다. gemini는 FS 접근이 없어 brief "경로 참조"가 안 통하므로 필요한 자료는 orchestrator가 MCP prompt에 직접 inline하고 그 사실을 brief·log에 적는다. FS 미접근 모델이 낸 *시스템 사실 주장*은 codex-critic/권위문서로 교차검증 후에만 채택한다(never-trust-upstream — 리뷰어 출력에도 동일 적용).
**근거**: pro-high가 큰/압축 프롬프트 모두 동일 400. Flash는 1회 성공했으나 문서 우선순위를 오추정, 같은 프롬프트로 pro-low는 정상 동작하며 더 날카로운 비평을 냈다(같은 프록시인데 pro-high만 막힘). pro-low조차 매뉴얼 용도(런타임 미적재 사람용 문서)를 오판해 "이론=토큰낭비"라는 틀린 전제로 소절 삭제를 권고 → 사실검증으로 불채택했다.
**worker**: gemini (프록시 장애·FS 미접근), codex-critic (사실 교차검증), orchestrator (폴백 강등·리뷰어 출력 검증)

## [2026-05-19] [repo-consistency-audit]
**교훈**: 다중 repo 일관성 감사에서 claude-main·codex-main을 **추상화 레이어로 분담**시키면(claude-main=의미·규칙 레벨, codex-main=파일·파서·코드 레벨) 같은 입력 중복 호출 대신 상호보완 커버리지가 나온다 — 이번에 codex만 검출(표준 brief→mat 파서가 worker 목적을 ` ```yaml `로 표시)·claude만 검출(manual↔mat 상태 우선순위 순서/단계 불일치)이 각각 진성 크리티컬이었고 둘 다 독립 검출한 항목(gemini 기본 모델 pro-high 충돌)은 신뢰도 최상으로 분류. 병렬 brief에 "다른 worker 결과 미참조" 명시는 codex result checklist에 그대로 확인됨. 또한 claude-main이 초기 가설 2건을 self-retract했어도 orchestrator가 인용 라인을 sources에 **직접 재대조**(never-trust-upstream을 worker 출력에도 적용)해야 false-positive·false-negative 둘 다 막힌다.
**근거**: 단일 worker였으면 크리티컬 3건 중 1건씩 누락. orchestrator 재검증에서 firstMeaningfulLine(task.go:499)·.mcp.json·routing.md:111을 직접 확인해 codex/claude 주장과 retraction을 모두 사실검증 후 취합.
**worker**: claude-main(의미·규칙 레이어), codex-main(파일·파서 레이어), orchestrator(레이어 분담 설계·인용 직접 재대조·취합)

## [2026-05-25] [autokakao-dup-guard]
**교훈**: 안전장치 코드의 codex-critic 비평을 반영할 때, Orchestrator가 비평을 **직접 재현 검증**하면(순수함수=단위테스트로, 구조적 결함=정적 grep/인덱스 비교로) 2차 worker 검수 호출 없이도 루프를 신뢰성 있게 종료할 수 있다 — 비평 맹신·맹기각 둘 다 회피. 이번엔 #3(정규화 충돌 `verify_room('스터디 2','스터디')=True`)을 단위로, #2(제목 후보 수집범위=메인창 전체→거짓양성)·#1(Enter가 포커스검증보다 먼저)을 정적으로 재현해 진성임을 확정하고, v2도 같은 방식으로 재검증(9케이스+정적 8항목 PASS) 후 사용자가 2차 검수 대신 수락. 더불어 안전장치는 **미확정 의존성(여기선 열린 방 헤더 AX 위치)을 파라미터+TODO로 외부화하고 미설정 기본값을 fail-closed**(전부 거부)로 두면, 라이브 검증 전 단계에서 절대 오발송이 안 나는 안전한 중간 산출물이 된다.
**근거**: codex High 3건이 모두 진성이었고 Orchestrator 재현으로 확정. read_open_room_title이 expected와 일치하는 후보를 메인창 어디서든 신뢰하던 v1은 "거짓 음성 방향" 주장과 달리 거짓 양성(오발송) 경로였음 — worker 자기평가도 never-trust-upstream로 교차검증해야 함. v2는 HEADER_* 미설정=항상 None=fail-closed로 안전하게 게이트.
**worker**: claude-main(구현·v2 반영), codex-critic(High3 비평), orchestrator(비평 직접 재현검증·fail-closed 수락 판단)

## [2026-05-25] [autokakao-jobs-demo]
**교훈**: 외부 GUI 자동화에서 "설계 단계의 가정"은 **라이브 테스트 전까지 미검증**으로 취급하라. 동명이인 안전장치를 브레인스토밍 때 전략 A(열린 방 헤더 제목 읽기)로 골랐지만, 라이브 probe 결과 KakaoTalk이 단일 창이라 헤더가 구분 가능한 AX 요소로 노출되지 않아 A는 원천 불가였다. 진짜 해법은 라이브 probe가 알려줬다 — ⌘F 검색 결과 셀(AXCell)의 `AXSelected`로 하이라이트를 읽어, room_title과 정확 일치하는 결과가 선택될 때까지 ↓ 후 Enter(전략 B). "첫 결과 ↓1회+Enter"는 '테스트' 검색이 '테스트1234'를 먼저 열어 오발송함을 라이브로 실증. 즉 GUI 자동화는 (1) 설계 가정에 과투자 말고 빨리 라이브 probe로 실제 AX 구조를 확인하고, (2) 안전장치는 '열고 나서 검증'(abort만 가능)보다 '정확한 대상을 애초에 선택'(B)이 더 강하다.
**근거**: 헤더 probe가 메인창 단일 창만 찾고(별도 창 없음) 열린 방 제목을 단일 요소로 못 줌. 반면 검색결과 probe에서 ↓1=테스트1234 selected, ↓2=테스트 selected가 깔끔히 노출돼 전략 B가 바로 구현됨. staging→--send 2/2 성공.
**worker**: orchestrator(라이브 probe·전략 전환·전략 B 구현), gemini(영수증·회의록 비전 정리)

## [2026-06-01] [harness-vup-reentry]
**교훈**: 외부 레퍼런스(harness)를 시스템에 도입하는 v-up에서, 6패턴을 통째로 받지 말고 **이 시스템 불변식으로 환원되는 것만 흡수하고 충돌하는 것은 "배제 근거를 design-basis(D6)에 명문화"**하는 방식이 정체성을 지킨다 — Pipeline/Fan-out·in/Expert Pool/Producer-Reviewer는 흡수(대부분 기존 암묵 구현, Fan-in 충돌해소만 신규), Supervisor·Hierarchical은 단일 orchestrator·worker간 무통신·file-as-memory와 충돌해 배제. codex-critic adversarial 리뷰가 진성 결함 2건(치명)을 잡음: ①재진입 분기를 result.md 유무로만 판단하면 status=waiting_<role>·늦은 응답·status↔log 불일치·외부 write_scope 재승인을 놓침 → 재정박에 brief+status 추가·분기 확장으로 해소, ②신설 불변식(INV11)의 grep이 `grep -lin`이라 "둘 중 하나만 맞아도 통과" → per-file `grep -q`+4패턴 positive+배제 negative check로 자동 FAIL 판정 가능하게 교정. 배제 근거 문구도 "Supervisor 개념 배제"가 아니라 "기존 orchestrator 위에 별도 long-lived 조정자/재귀 위임 **계층 추가**를 배제"로 정밀화해야 정확(orchestrator 자신이 이미 중앙 조정자이므로).
**근거**: orchestrator가 critic ISSUE 6건을 사실검증(never-trust-upstream을 리뷰어에도 적용) → #3만 PASS, 5건 진성 → 전부 반영. 자가점검 INV11a/b/c 신규 PASS, INV1~10 회귀 없음. 새 상시로드 비용은 CLAUDE.md 1줄 포인터뿐, 본문은 orchestrator-rules(온디맨드)·routing(라우팅시)·design-basis/invariants(게이트)에 배치.
**worker**: orchestrator(흡수/배제 설계·라이브 파일 편집·ISSUE 사실검증·자가점검), codex-critic(변경안 adversarial 리뷰 5 ISSUE)

## [2026-06-01] [model-policy-cleanup]
문서 일관성 변경(예: 모델 버전 문자열 → 별칭화)은 "정책 섹션"만 고치면 안 된다. 같은 식별자가 워커 상세·비용 설명·예시 등 여러 위치에 흩어져 있어, 한 곳만 바꾸면 같은 파일 안에서 정책↔본문이 모순된다. codex-critic이 routing.md의 잔존 핀(:62 claude-opus-4-7, :65 Opus 4.7, :120 gpt-5.4-mini)을 잡았다. → 표기 정책을 바꿀 땐 `grep`으로 그 식별자의 전 등장 위치를 먼저 훑고 일괄 처리할 것. 또한 "결정적/영속" 같은 단정어는 환경 설정(config·env·profile)으로 바뀔 수 있는 값엔 과장이므로 피한다.

## [2026-06-02] [gemini-backend-agy]
"pro-high 쓰지 마라"(D4/INV9) 같은 **환경 한계발 금지 규칙**은 그 환경(백엔드)이 바뀌면 근거가 사라진다. pro-high 제외 사유는 옛 antigravity-claude-proxy의 `400 INVALID_ARGUMENT`였는데, 백엔드를 `agy` CLI로 바꾸니 pro-high가 정상 작동(spike 실증). → 금지 규칙엔 **"무엇 때문에 금지인지(원인 계층)"를 함께 적어야**, 원인이 사라졌을 때 안전하게 해제할 수 있다. 또 모델 셀렉션이 도구마다 다름을 확인: agy는 모델이 **전역·계정단위**(`/model`)라 per-call 핀 불가 → worker별 다른 모델 동시 사용은 안 되고, gemini 전용 전역을 pro-high로 고정해 운용. 마이그레이션은 D4·INV9·INV10·routing·validate C6를 **한 묶음으로** 갱신해야 내부 모순(validate가 새 정본을 FAIL)이 안 생긴다.
**근거**: agy spike S1 GREEN + 3자 검수(codex #8이 "옛 정책과 충돌" 지적 → 검증하니 정책을 갱신해야 하는 것이었음). backends.json이 gemini 호출 정본, mcp__gemini-pro__/mcp__gemini__ 브리지 폐기.
**worker**: orchestrator(마이그레이션·라이브 편집), codex-critic+gemini=agy(검수)

## [2026-07-27] [add-ollama-worker]
**교훈**: 새 worker 추가가 반드시 새 설계 결정(design-basis D항목)이나 새 불변식(INV)을 요구하는 건 아니다 — 기존 어댑터+디스패처 패턴(gemini의 cli/api 슬롯)을 재사용하면, backends.json에 워커 레코드 1개 + `adapters/<w>_api.sh` 1개만 추가하고 나머지는 병기(편의 사본) 동기화로 끝난다. capability-profile §3 "담당명 병기 사본을 전부 동기화"의 대상은 **워커 목록·슬롯 배정을 나열하는 파일**(profile·routing·CLAUDE·README + 비용표 approval-policy)이고, **구조 파일**(orchestrator-rules·system-invariants·design-basis)은 §4대로 손대지 않는다 — 거기서 gemini가 보이는 건 "목록"이 아니라 gemini 전용 정책/불변식 맥락이라 새 워커가 자동 편입 대상이 아니기 때문. 로컬 워커(ollama)의 함정: **비용=0이라 승인 게이트 밖이라고 오해하기 쉬움** → 게이트 기준은 "비용≠0"이 아니라 "worker 여부"이므로 workers_approved 대상 동일(approval-policy에 명시). 어댑터는 gemini_api.sh 인터페이스(`<brief-file>`→stdout 텍스트, exit 0)를 그대로 따르면 디스패처(call_worker.sh) 수정 불필요 — 단 CLI allowlist(agy|codex|claude)는 로컬 데몬 바이너리를 안 받으므로 로컬 HTTP는 반드시 **api 경로**(adapters/ 스크립트)로 태워야 통과한다.
**근거**: backends.json jq 유효성 + INV9(gemini=agy·pro-high) 잔존 확인 PASS. api.ref 실존 확인. required_env=[]로 localhost는 키 검사 우회(로컬은 인증 불필요). 폴백 없음(단일 로컬 백엔드).
**worker**: orchestrator(설계 결정 4문항 확인·정본 6파일 동기화·구조파일 비편입 판단·검증)

## [2026-08-25] [landing-function-license-flow]
**교훈**: 소형 self-hosted 모델의 지시 무시는 **프롬프트 구조가 아니라 user 페이로드 절대 길이**가 원인이다. 12,688자 brief에서 요구 형식 8문항 중 0건 응답(대상을 '완성된 리뷰'로 오인해 칭찬·요약 반환)했을 때, 세 가설을 순서대로 실측해 원인을 좁혔다 — ①모델 용량? qwen2.5:7b(gemma3의 1.8배)로 교체해도 0/8, 실패 양상만 바뀜(칭찬→재요약) → 기각. ②지시와 데이터가 한 텍스트에 섞여서? 어댑터를 `/api/chat`으로 바꿔 system/user를 분리해도 0/8 → 기각. ③길이? **동일 system을 고정한 채 user만 219·500·1,500·4,000자로 줄이니 전부 8/8, 11,585자만 0/8** → 확정. 즉 흔한 처방인 '모델 업그레이드'와 'system 프롬프트 분리'가 둘 다 무효였고, 값싼 처방(입력 축약·분할 호출)이 유효했다. 회피 패턴: 소형 모델에 긴 대상을 검증시킬 때는 **판정에 필요한 최소 발췌만 전달하거나 1문항씩 분할**한다(본 건에서 설계 11,000자 → 발췌 219자로 1/40 축약).
**부수 교훈 1 — 형식 준수와 판정 정확도는 별개**: 분할 호출로 형식은 6/8까지 올랐으나 판정 내용은 3/8이었다. 더 나쁜 것은 **YES 3건은 전부 정답, NO 3건은 전부 오답**이고 근거 제시 요구를 무시해 `NO` 한 단어만 반환한 점이다. 그대로 수락했다면 존재하지 않는 결함 3건을 산출물에 만들어냈을 것이다 — **형식이 맞을수록 오히려 위험**하다(그럴듯해 보이므로). 소형 모델의 부정 판정은 반드시 Orchestrator가 소스로 재대조해야 한다(never-trust-upstream).
**부수 교훈 2 — envelope의 model 필드는 실사용 모델이 아니다**: `call_worker.sh:59`가 `backends.json`의 정적 값을 읽어 찍으므로, env(`OLLAMA_MODEL`)로 모델을 바꿔도 envelope엔 반영되지 않는다. 모델 교체 실험 시 envelope만 보면 '안 바뀌었다'고 오판한다 — API 응답의 `model` 필드로 실사용 모델을 확인할 것.
**부수 교훈 3 — 사전 정찰 결론을 상한으로 못박지 말 것의 재확인**: Orchestrator 정찰이 '토큰 보유 19개 / `--<page>-*` 접두가 관례'라 기재했으나 워커가 실측으로 17개·접두는 관례 아님(진짜 불변식은 '래퍼 클래스 스코프 로컬 선언')을 검출했다. brief에 '정찰 결과는 상한이 아니므로 직접 재확인할 것'을 명시한 것이 회수됐다. 정정은 sources 원본에 즉시 반영해야 후행 워커가 틀린 전제를 물려받지 않는다.
**근거**: 실험 3단계 전부 자체 실측(`/api/tags` 모델 스펙 확인, 동일 brief 교차 투입, 길이 스윕 219~11,585자). 어댑터 변경은 하위호환 회귀 2건(마커 없음→`OK`, 마커 있음→`READY`) 및 INV1-12 전체 PASS로 검증. 워커 산출물 판정은 `common.css` 인용 줄번호 6건·색상 12건·4관점 매핑을 Orchestrator가 소스에서 직접 재확인.
**worker**: claude-main(설계·정찰 오류 2건 검출), ollama(검증 실패 — 형식·정확도 양쪽), orchestrator(가설 3단계 실측·원인 규명·어댑터 수정·정본 5파일 동기화·소스 재대조)

## [2026-08-25] [dispatcher-crlf-fix]
**교훈**: 도구 출력의 줄바꿈 형식은 **플랫폼별 빌드 차이**로 조용히 달라진다. WinGet `jq-1.8.2`(Windows)는 stdout에 CRLF를 쓰는데, 이게 디스패처의 워커 2개를 동시에 죽이고 있었다. 핵심은 **왜 오래 잠복했는가**다 — 명령치환 `$(jq ...)`는 후행 `\r\n`을 공백으로 깎아내므로 `call_worker.sh`의 단일값 읽기 13곳이 전부 멀쩡하다. 실제 파손은 `while IFS= read -r` 루프 3곳뿐이고, 거기서도 **배열의 마지막 원소만 우연히 무사**하다(`<<<`가 후행 개행 제거). 그래서 3원소 배열이면 `--alpha\r`·`--beta\r`·`--gamma`로 앞 두 개만 깨져 증상이 산발적으로 보인다. → 외부 도구 출력을 `read` 루프로 도는 곳은 **`$()`가 멀쩡하다는 이유로 안전하다고 추정하지 말 것**. 처방은 `IFS=$'\r'`(후행 CR을 필드 구분자로 흡수, LF-only 빌드에선 no-op이라 양방향 이식성).
**부수 교훈 1 — `set -u` + 간접확장 `${!var}`는 CR을 만나면 경고가 아니라 즉사다**: 53행 주석은 "경고만(primary가 죽고 나서야 폴백 불가를 아는 것을 방지)"이라 적혀 있었으나, `${!_fe:-}`가 `GEMINI_API_KEY\r`을 변수명으로 받으면 `invalid variable name`으로 `set -e`가 발동해 **envelope 출력 전에 스크립트가 종료**된다(exit 1, stdout 빈 문자열). **주석의 의도와 실제 동작이 갈리는 지점**이므로, 간접확장의 입력이 외부 도구 출력이면 반드시 정규화 후 사용한다.
**부수 교훈 2 — 잠복 결함은 primary가 살아 있는 동안 보이지 않는다**: 같은 버그가 codex-main의 **CLI 폴백**(`exec\r`·`-\r`)에도 있었으나 MCP가 primary라 한 번도 발동하지 않았다. 발견 경로는 gemini 조사 중 **워커별 전수 조사**였다 — 한 워커의 증상을 고칠 때 같은 코드 경로를 쓰는 다른 워커를 함께 점검해야 동종 결함이 잡힌다. 실제로 이번 수정 5줄로 gemini와 codex-main 폴백이 **동시에** 복구됐다.
**부수 교훈 3 — `od -c`는 실제 CR 바이트와 두 글자 이스케이프를 구분하지 못한다**: 패치 1차 시도에서 `IFS=$'\r'`에 리터럴 CR 바이트(0x0D)를 써버렸는데, `od -c`가 둘 다 `\r`로 표시해 검증을 통과시켰고 테스트만 계속 실패했다. `cat -A`로 보니 `IFS=$'^M'`이 드러나 원인이 잡혔다. → **셸 이스케이프를 프로그램으로 생성할 땐 검증에 `cat -A`를 쓴다**(`od -c`는 이 구분에 부적합). 같은 함정이 이 교훈을 learnings.md에 기록할 때 재발했다 — 파일에 `\r`를 쓰려다 실제 CR 바이트가 6줄에 박혔고, `cat -A`의 줄 중간 `^M` 검사로 잡아 되돌렸다.
**부수 교훈 4 — 백엔드 정상성과 배관 정상성을 먼저 분리하라**: `agy` 직접 호출은 `OK`·exit 0(정상), 디스패처 경유는 exit 1(실패). 이 대조 하나로 "gemini 워커가 죽었다"가 아니라 "디스패처가 깨졌다"로 문제가 좁혀진다. 이 분리를 먼저 하지 않으면 워커 삭제(잘못된 처방)로 갈 수 있다 — 실제로 삭제를 진행했다가 롤백한 경위가 있다.
**근거**: `bash -x` 추적으로 사망 지점 확정(53행 `read -r _fe` → `$'GEMINI_API_KEY\r'`). CR 격리 실증 — `codex exec -`는 exit 0·`OK` 반환, `codex $'exec\r' $'-\r'`는 exit 2. 수정 전후 대조(HEAD 원본, 동일 입력): gemini `invalid variable name`/exit 1 → `status:ok`/exit 0/`stdout:"OK"`, codex-main 폴백 `unrecognized subcommand '-'`/exit 2 → `status:ok`/exit 0/`stdout:"OK"`. 회귀 4건(미정의 role·MCP 직접호출 거부·brief 부재·`..` 차단)·CLI allowlist 유지 확인. `bash -n` PASS, CRLF 줄바꿈 보존(176/0), **불변식 스크립트 출력이 수정 전후 `diff` 무차이**(회귀 없음).
**worker**: orchestrator 단독(원인 규명·수정·검증). 워커 호출 없음 — 승인 게이트 대상 아님.

## [2026-08-25] [dispatcher-die-envelope + auth-fact-correction]
**교훈**: `set -e` 스크립트에서 **마지막 출력문이 실패하면 그 뒤의 `exit <code>`가 통째로 무시된다** — 의도한 종료코드가 실패한 명령의 종료코드로 조용히 바뀐다. `call_worker.sh`는 `run_backend`가 `die`로 죽으면 `$()` 서브셸이 끝나 envelope 변수가 빈 문자열이 되는데, 그걸 `jq --argjson`에 넘겨 jq가 exit 2로 실패하고 `set -e`가 발동해 다음 줄 `exit 1`에 **도달조차 못 했다**. 결과적으로 die가 지정한 고유 코드(3=디스패처 비경유, 4=스크립트 없음, 7=allowlist 위반 등) **5종이 전부 exit 2로 뭉개져** 호출자가 실패 원인을 구분할 수 없었다. → 실패 경로의 출력문은 **입력이 비었을 때를 반드시 방어**하고, 종료코드는 출력 성공 여부와 독립적으로 보존한다(여기선 빈 값이면 envelope을 합성하고 `final_rc`를 따로 들고 exit).
**부수 교훈 1 — "exit code는 정확히 전달된다"를 눈으로 확인하지 않고 단정하지 말 것**: 1차 점검에서 이 결함을 "envelope만 비고 exit code는 정상이라 위험 낮음"으로 보고했는데, `bash -x`로 끝까지 따라가 보니 `prc=7`까지는 맞게 잡히고 **그 다음 jq 실패로 코드가 덮이는** 구조였다. 중간 변수가 올바른 것과 최종 종료코드가 올바른 것은 별개다 — `echo $?`를 실제로 찍어봐야 안다.
**부수 교훈 2 — 결함의 트리거 조건을 좁히면 우선순위가 바뀐다**: 처음엔 "fallbacks=0 워커에서 빈 envelope"이라 기술했으나, 픽스처로 나눠 보니 **정상 실행 후 실패는 envelope이 멀쩡**했고 오직 `run_backend` **내부 die**(5곳)만 문제였다. 반대로 `run_backend` **이전** die(role 미정의·brief 부재·`..` 차단)는 envelope이 없는 게 정상 동작이라 고칠 대상이 아니다. 같은 `die`라도 **호출 위치가 계약을 가른다**.
**부수 교훈 3 — 환경이 소유한 사실은 단정형으로 문서에 굳히지 말 것**: `capability-profile`·`routing`이 codex를 "401로 실패한다"고 단정해 뒀는데, 그 사이 `codex login`이 완료돼 **살아 있는 워커를 죽었다고 안내**하는 상태가 됐다(D7의 "환경이 소유하는 사실" 원칙과 같은 방향). 정정은 append-only 규약대로 **기존 이력을 고치지 않고 정정 항목을 추가**하고, 재발 방지로 서술을 **조건형("인증이 없으면 401 → 소스 실측으로 대체")으로 전환**했다. 조건형이면 인증이 다시 풀려도 문서가 계속 참이다.
**근거**: die 5종 전수 재현 후 수정 전후 대조 — 수정 전 exit 전부 2, 수정 후 3·7·7·7·4로 각 die 코드 보존 + 전부 유효 envelope(`status:error`, `exit_code` 일치). 회귀: 성공 경로(gemini `status:ok`/exit 0/`"OK"`), 실행 후 실패(envelope·stderr 보존), run_backend 이전 die 3종(exit 2·6·6, envelope 없음 = 정상). 인증은 `codex login status`=`Logged in using ChatGPT`·`auth.json` 존재·MCP 스모크 3회 전부 `OK`로 확인(`OPENAI_API_KEY`는 미설정이나 `auth.json`만으로 동작). `bash -n` PASS, 4개 파일 CRLF 보존·bare LF 0, **불변식 출력 수정 전후 `diff` 무차이**.
**worker**: orchestrator 단독(재현·수정·검증·문서 정정). 워커 호출 없음 — 승인 게이트 대상 아님.
