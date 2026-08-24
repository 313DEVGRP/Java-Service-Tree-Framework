# Changelog

이 파일은 MultiAgent orchestration 시스템의 주요 변경을 기록한다.
형식은 [Keep a Changelog](https://keepachangelog.com/), 버전은 [Semantic Versioning](https://semver.org/lang/ko/)을 따른다.

## 1.4.0 - 2026-07-27

### Added
- **`ollama` 워커 추가 — reviewer 슬롯 보조(자체호스팅)** — 벤더 쿼터에 묶이지 않는 독립
  검증자 확보로 codex-critic의 교차 다양성 보강. 주 검증자는 codex-critic 유지, ollama는 보조
  ("검증 1회 원칙"은 슬롯 단위 적용). 기본 모델 `gemma3`(`backends.json`에서 교체 가능),
  백엔드 = HTTP API(`_shared/adapters/ollama_api.sh`, env `OLLAMA_HOST`로 호스트 재정의).
  기존 어댑터+디스패처 패턴 재사용 — 새 design-basis 결정·새 INV 없이 `backends.json` 워커 레코드
  1개 + 어댑터 1개 추가로 완결. 근거: `_shared/learnings.md` `[2026-07-27] [add-ollama-worker]`.

### Changed
- 담당명 병기 사본 동기화 — `capability-profile.md`(배정 정본)·`routing.md`·`CLAUDE.md`·`README.md`
  + 비용표 `approval-policy.md`. 구조 파일(`orchestrator-rules`·`system-invariants`·`design-basis`)은
  미편입(capability-profile §4 갱신 절차).

### Fixed
- **`ollama` 도입 시 기재 오류 정정(2026-07-28)** — 'localhost:11434 로컬·오프라인'으로 적었으나
  어댑터 실제 기본값은 자체호스팅 **원격** 데몬이다. '벤더 쿼터 없음'은 유효하나
  '오프라인·네트워크 불필요'는 성립하지 않는다 — 네트워크 단절 시 이 슬롯 사용 불가.
  `capability-profile.md`·`routing.md`·`CLAUDE.md`·`README.md` 병기 사본 동일 정정.

### Note
- 로컬·무료 워커도 승인 게이트 대상이다. 게이트 기준은 "비용≠0"이 아니라 **"worker 여부"**이므로
  `ollama`도 `workers_approved`에 명시적 기록이 필요하다(`approval-policy.md`).
## 1.3.0 - 2026-07-13

### Added
- **라우팅 2층 분리 — `_shared/capability-profile.md` 신설(가변층)** — 능력 슬롯
  (strategist·engineer·computer-use·reviewer·multimodal) → 담당 워커 배정의 정본.
  신모델 출시·판정 변경 시 프로필만 갱신(근거·날짜 필수, 이력 append-only) — routing.md의
  슬롯 정의는 불변. 근거: design-basis D9 (2026-07-13 외부 리뷰 10건 종합 판정).
- **computer-use 슬롯 신설** — 브라우저 조작·도구 워크플로우 자동화를 독립 라우팅
  (현 배정: codex-main).

### Changed
- routing.md decision tree를 슬롯 기반으로 재편 — strategist(기획·설계·디자인·전략·문체)
  = claude-main, engineer(대규모 구현·테스트) = codex-main. 종전 "메인 코딩=claude-main,
  보조 구현=codex-main" 구도에서 무게중심 이동. 최소 worker set 표 동기화.
- validate에 C5b(2층 라우팅: routing→profile 참조 + 슬롯 5종) 추가, C1에 프로필 포함.

## 1.2.2 - 2026-07-04

### Fixed
- **gemini 워커 폴백 실패 사유 유실** — 디스패처(`call_worker.sh`)가 api 폴백의 필수 env
  (`GEMINI_API_KEY`) 부재 시 실패 사유 없이 죽던 문제를 에러 envelope 반환으로 수정,
  호출 시작 시 폴백 불가 사전 경고 추가.

### Changed
- routing.md gemini — 소스·다중파일 검토 인라인 필수(agy 헤드리스 300s 타임아웃 실측),
  폴백 조건(`GEMINI_API_KEY`) 명문화, 시간 제한 작업 전 경량 스모크 권장.

## 1.2.1 - 2026-07-03

### Fixed
- **gemini(agy) 워커 프롬프트 미전달 수정** — Antigravity CLI 1.0.16에서 `-p` 단축 플래그가
  제거되어 backends.json의 `args_template: ["-p", …]`가 프롬프트를 조용히 무시(모델 미호출·사용량 0).
  `["--prompt", …]`로 교정. 증상: gemini 워커가 온보딩 인사만 반환.

## 1.2.0 - 2026-06-28

### Added
- **opt-in goal 요금가드 배선(`--with-guard`)** — 설치 시 `--with-guard`를 주면 `.claude/settings.json`에
  Stop 훅(`coach --hook`)이 주입된다. `/goal` 자율 루프가 주간 사용량 한도에 닿으면 자동 정지(루프
  중에만 — `stop_hook_active` 게이트). 기본 미설치, 런타임 on/off=`coach guard on/off`. 정책은 `coach`
  (usage-coach, codexbar 의존)가 갖고 미설치·조회실패는 fail-open(작업 안 죽임).

## 1.1.0 - 2026-06-10

카파시(Karpathy) 4원칙을 층별로 도입. 기존 규칙과 충돌 없음(보강).

### Added
- **CLAUDE.md "운영 원칙 (Operating Principles)" 섹션** — 4원칙(Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution) verbatim 차용 + 층별 적용 규칙. Orchestrator 전용 풀버전.
- **`_templates/worker-brief.md` "Worker 행동 규약" 고정 블록** — 워커층 번역형: ②③ 그대로, ①은 가정 명시·표면화(워커는 one-shot이라 사용자 질문 채널 없음), ④는 오케스트레이터 전용.
- **`_templates/worker-result.md` 체크리스트 항목** — "가정·불일치가 Issues/Caveats에 표면화됨".
- **design-basis D8 / system-invariants INV12** — 층별 적용 결정 명문화 + 자가점검.
- **`NOTICE`** — 출처·라이선스 표기 (multica-ai/andrej-karpathy-skills, MIT 선언·LICENSE 파일 부재).

## [1.0.1] - 2026-06-01

모델·추론 정책 표기 정리(문서 patch). 동작 변경 없음.

### Changed
- **모델 식별자 별칭화** (`_shared/routing.md`): claude-main을 버전 문자열(`claude-opus-4-7` 등) 대신 별칭 `opus`로 표기 — 모델이 올라가도 문서 갱신 불필요. codex 예시 일반화, gemini는 `gemini-3.1-pro-low` 핀 유지 + "프록시 업그레이드 시에만 갱신" 노트.
- **claude-main 추론 강도(effort) 명문화**: `effort` 핀 없음 → 세션 `/effort` 상속(현 기본). 고정하려면 frontmatter `effort:`.

### Added
- **design-basis D7**: 모델 식별자 표기 정책(별칭 원칙 / gemini 핀 예외·세부는 D4 정본 / effort 비대칭 근거).

### Verification
- codex-critic adversarial 검수: 치명 0, 권장 3 반영(잔존 핀 제거 포함). INV9/INV10/INV11 PASS, 회귀 없음.

## [1.0.0] - 2026-06-01

첫 버전 태깅. 기존 실사용 시스템을 1.0.0 기준선으로 고정하고, harness(revfactory) 참고 버전 업그레이드를 함께 반영한다.

### Added
- **작업 재진입 프로토콜** (`_shared/orchestrator-rules.md` §3): 콜드세션이 끝난 작업에 다시 들어갈 때 재정박(re-anchor) → 6분기 판단 → 에러 후 진행. `status↔log 불일치`는 다른 분기보다 먼저 적용하는 정규화 단계로 명시.
- **토폴로지 4패턴표** (`_shared/routing.md`): Pipeline / Fan-out·Fan-in / Expert Pool / Producer-Reviewer + Fan-in 규칙.
- **CLAUDE.md** Task Lifecycle에 재진입 프로토콜 포인터.
- **불변식 INV11** (`_shared/system-invariants.md`): 재진입·토폴로지 규정 자동 자가점검(11a/b/c).
- **design-basis D6**: 4패턴 채택 + Supervisor·Hierarchical Delegation 배제 근거.

### Excluded (설계 결정)
- Supervisor·Hierarchical Delegation 패턴: 단일 orchestrator·worker간 무통신·file-as-memory와 충돌하여 미채택 (근거 D6).

### Baseline (1.0.0 시점 핵심 구조)
- 고정 4-worker pool (claude-main / codex-main / codex-critic / gemini), Claude Code 세션 = orchestrator.
- file-as-memory (런타임 상태 0): task / context / log / brief / result.
- 승인 게이트(`workers_approved`), 외부 쓰기 4조건, progressive disclosure(게이트 로드), 권위 우선순위(CLAUDE.md > routing/approval/orchestrator-rules > 매뉴얼).

### Verification
- 배선(INV11a/b/c) PASS · 회귀 없음, 탁상 분기 커버리지, 실전 콜드세션 3/3 PASS, codex-critic adversarial 리뷰 5 ISSUE 반영.

<!-- 릴리스 링크: 상위 starter(netwaif/multi-agent-starter)에 실제 존재하는 태그만 링크한다.
     해당 저장소는 v1.0.1 다음 v2.1.0으로 건너뛰었고(현재 v3.5.0), 이 저장소의 1.1.0~1.4.0은
     상위 릴리스와 대응하지 않는 로컬 번호다. 실측 2026-08-24: v1.0.0·v1.0.1만 HTTP 200,
     v1.1.0~v1.4.0은 404. 없는 태그를 링크하면 깨진 참조가 되므로, 해당 버전은 링크 정의를
     달지 않고 헤딩에서도 대괄호를 뺀다(Markdown 미정의 참조는 대괄호가 그대로 렌더됨). -->

[1.0.1]: https://github.com/netwaif/multi-agent-starter/releases/tag/v1.0.1
[1.0.0]: https://github.com/netwaif/multi-agent-starter/releases/tag/v1.0.0
