---
type: concept
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [Worker Pool, 워커 풀]
---

# Worker Pool

[[multiagent-orchestration-system]]의 ①계층 — 외부 모델을 호출하는 정식 워커 집합. 전원 승인 게이트(`workers_approved`) 대상이다. [[agent-layer-separation]]로 ②계층과 구분된다.

## 구성 (2026-07-29 확인)

| 워커 | [[capability-slot]] | 호출 방식 | 모델 |
|---|---|---|---|
| claude-main | strategist | native (`.claude/agents/claude-main.md`) | host-default (opus) |
| codex-main | engineer · computer-use | MCP `mcp__codex__codex` (폴백 CLI) | codex-default |
| codex-critic | reviewer (주) | MCP `mcp__codex__codex` | codex-default |
| gemini | multimodal | `agy` CLI (폴백 api) | gemini-3.1-pro-high |
| ollama | reviewer (보조) | HTTP API | gemma3 |

claude-main만 `.claude/agents/` 파일로 존재하고 나머지는 MCP/CLI/API로 호출된다. 호출 스펙 정본은 `_shared/backends.json`.

## 쓰기 권한

| 워커 | 기본 | 외부 repo |
|---|---|---|
| claude-main | Orchestrator 경유 | 불가 |
| codex-main | `tasks-only` | 조건부 (4조건) |
| codex-critic · ollama · gemini | 없음 | 불가 |

codex-main 외부 repo 쓰기 4조건 — `target_repo` 명시 + `write_scope` 명시 + `workers_approved` 승인 + `log.md`에 `[APPROVAL]` 별도 기록. 하나라도 누락되면 `tasks/` 내부에 diff·patch로만 산출한다.

## 검증 독립성

reviewer 슬롯은 **자기검수 회피**가 설계 의도다. codex flavor에서 codex-critic이 금지 워커인 이유이며(오케스트레이터와 같은 벤더), ollama는 벤더 쿼터에 묶이지 않는 보조 검증자로 2026-07-27 추가됐다.

주의 — ollama는 자체호스팅이지만 기본값이 **원격** 데몬(`mad.hyper-mig.com:11434`)이다. '쿼터 없음'은 맞지만 '오프라인 가능'은 성립하지 않는다. 네트워크 단절 시 이 슬롯은 사용 불가.

## 관련

- [[worker-dispatcher]] — cli/api 워커의 실제 실행 경로
- [[multiagent-subagent-audit-2026-07-29]] — 구성·정본 동기화 실측 확인
