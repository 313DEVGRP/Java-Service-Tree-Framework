---
type: concept
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [call_worker.sh, 디스패처]
---

# 워커 디스패처 (call_worker.sh)

`_shared/adapters/call_worker.sh` — `backends.json`을 읽어 **cli·api 타입 워커만** 실행하는 디스패처. native(claude-main)와 mcp(codex) 워커는 이 경로를 타지 않는다.

출력은 JSON envelope이며, Orchestrator가 envelope의 stdout을 `result.md`에 기록한다([[worker-pool]]의 `result_capture: envelope`).

```bash
bash _shared/adapters/call_worker.sh <worker> <brief-file>
```

## 방어장치 (2026-07-29 실측)

신뢰할 수 없는 brief 내용이 셸로 흘러드는 것을 막는 층이다.

| 검사 | 내용 |
|---|---|
| command allowlist | `agy`·`codex`·`claude`만 실행 허용. 위반 시 exit 7 |
| 경로 traversal | brief 경로에 `..` 금지 (exit 6), `api.ref`에도 `..` 금지 |
| api.ref 범위 | `adapters/` 내부만 (exit 7) |
| codex git 요구 | codex 워커는 git 필수. 없으면 명확히 실패 (exit 8) |
| cwd 격리 | gemini·ollama는 `isolated_tmp` — 작업 디렉토리 밖에서 실행 |
| write_policy | gemini·ollama는 `none` |

codex의 git 요구는 안전망이다. `MULTIAGENT_CODEX_SKIP_GIT=1`로 우회할 수 있지만 위험을 감수하는 옵트아웃이다.

## 폴백 체인

`backends.json`의 `fallbacks` 배열로 정의된다. gemini는 `agy` CLI → api(`gemini_api.sh`, `GEMINI_API_KEY` 필요, 재시도 2회), codex-main은 MCP → CLI(`codex exec -`, stdin으로 brief).

## 관련

- [[multiagent-subagent-audit-2026-07-29]] — 워커 CLI 4개 PATH resolve 및 방어장치 확인
