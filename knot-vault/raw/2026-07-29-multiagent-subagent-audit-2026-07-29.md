# 멀티에이전트 + 서브에이전트 시스템 점검 (2026-07-29)

대상: `C:\DEV\sourcecode\Java-Service-Tree-Framework` — 파일 기반 MultiAgent 오케스트레이션 시스템 (flavor: claude).

## 점검 방법

시스템에 내장된 자가점검 `_shared/system-invariants.md`(INV1–INV12)의 bash 블록을 직접 실행했다.
문서 요약이 아니라 실측. 결과: **핵심 항목 전부 PASS**.

INV5 및 flavor 교차점검(INV12e/f)은 유지보수자 전용이며, 외부 매뉴얼(`multi-agent-manual.txt`)과
generator templates가 이 설치본에 없어 스크립트가 정상적으로 건너뛴다 — 공개 설치본에서는 이게 정상 동작이다.
루트의 `Multi_Sub_Agent_USE_Manual.pptx`는 INV5가 대조하는 `multi-agent-manual.txt`가 아니라서 대조 대상이 아니다.

## 핵심 구조: 두 계층 분리

`.claude/agents/` 폴더에 **목적이 다른 두 계층**이 공존한다. 이것이 이 시스템에서 가장 혼동하기 쉬운 지점이다.

| 계층 | 구성원 | 승인 게이트 | 호출 방식 |
|---|---|---|---|
| ① Worker Pool (멀티에이전트) | claude-main, codex-main, codex-critic, gemini, ollama | `workers_approved` 필수 | claude-main=native, codex=MCP, gemini=agy CLI, ollama=HTTP API |
| ② 도메인 서브에이전트 | frontend-expert, backend-expert | 대상 아님 | 일반 Claude Code 서브에이전트 |

- ①은 **능력 슬롯에 배정**되며 슬롯 정의는 불변(안정층 `_shared/routing.md`), 배정은 가변층 `_shared/capability-profile.md`.
- ②는 `backends.json`에 등록하지 않고 정본 5개 문서도 건드리지 않는다. 도메인 전문성은 슬롯이 아니므로 ①에 넣지 않는다.
- ②를 추가하려면 `.claude/agents/README.md` 표에 한 줄 + `<name>.md` 파일만. ①을 추가하려면 capability-profile 갱신 절차(정본 5개 동기화).

## 슬롯 배정 (2026-07-29 확인)

strategist=claude-main · engineer/computer-use=codex-main · reviewer=codex-critic(주)+ollama(보조) · multimodal=gemini.

정본 5개 파일(`capability-profile.md` · `backends.json` · `routing.md` · `CLAUDE.md` · `README.md`)이 상호 일치함을 확인.

## 실행 환경

워커 CLI 4개(`codex` `agy` `ollama` `python3`) 모두 PATH resolve 확인.
디스패처 `_shared/adapters/call_worker.sh`의 방어장치: command allowlist(`agy|codex|claude`), brief 경로 `..` 차단,
`api.ref`는 `adapters/` 내부만, codex 워커는 git 요구(`MULTIAGENT_CODEX_SKIP_GIT=1`로만 우회).

## 작업 폴더 규약 준수

3개 작업(arms-i18n-label-audit, landing-calendar-i18n, landing-calendar-redesign) 모두 `status: done`.
`tasks/<task>/workers/<role>/brief.md` 워커별 폴더 구조 준수 — CLAUDE.md가 금지한 납작한 `<role>_brief.md` 형태 위반 0건.

## 관찰: 계층 경계의 실전 처리

`landing-calendar-*` 두 작업에서 frontend-expert(②계층)가 `workers/` 아래에 폴더를 갖는다.
이는 위반이 아니다 — task.md에 "2계층 도메인 서브에이전트라 workers_approved 게이트 대상이 아니나,
실제 호출이 발생하므로 투명성 위해 기록"이라 명시돼 있다.

즉 **승인 게이트 대상 여부**와 **산출물 기록 위치**는 별개 축이다. 게이트 밖 에이전트도 호출 사실은 기록하는 것이
이 시스템의 실전 관행이며, Producer-Reviewer 토폴로지에서 reviewer 자리에 codex-critic 대신
도메인 서브에이전트를 넣은 사례이기도 하다.

## 열린 질문

- ②계층 산출물을 `workers/` 아래 두는 관행을 규약(CLAUDE.md·task-folder.md)에 명문화할지, 관행으로 남길지.
- INV 목록에 ②계층 관련 불변식이 없다 — 두 계층 혼입(② 에이전트가 backends.json에 등록되는 사고)을 막는 기계 검사 추가 여부.
