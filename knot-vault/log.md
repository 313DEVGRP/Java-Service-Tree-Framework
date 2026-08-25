# log

append-only 연대기. 항목 prefix: `## [YYYY-MM-DD] ingest|query|lint — 제목`. 수정·삭제 금지.

## [2026-07-29] ingest — 멀티에이전트 + 서브에이전트 시스템 점검

소스: `raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md` (vault 최초 ingest).

생성한 페이지 (8):

- source: `multiagent-subagent-audit-2026-07-29`
- entity: `multiagent-orchestration-system`, `java-service-tree-framework`
- concept: `agent-layer-separation`, `worker-pool`, `domain-subagent`, `capability-slot`, `system-invariants`, `worker-dispatcher`

갱신: `index.md`(8줄 등재).

핵심 takeaway — `.claude/agents/` 한 폴더에 승인 게이트 대상인 Worker Pool과 게이트 밖 도메인 서브에이전트가
공존한다(`agent-layer-separation`). 파생 원리로 '승인 게이트 대상 여부'와 '산출물 기록 위치'는 별개 축임을 정리.

표면화한 열린 질문 2건 — ②계층 산출물의 `workers/` 배치를 규약에 명문화할지, 두 계층 혼입을 막는 INV 추가 여부.

