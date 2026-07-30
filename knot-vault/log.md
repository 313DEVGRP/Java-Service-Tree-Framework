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

## [2026-07-30] ingest — 이동민 경력 요약

소스: `raw/2026-07-30-leedongmin.md`.

생성한 페이지 (2):

- source: `leedongmin-career`
- entity: `leedongmin`

갱신: `index.md`(2줄 등재).

가드 경위 — step 1 클린트리 가드에 걸렸으나 동시 실행이 아니었다(시연용 더미 삭제 + 신규 소스 추가로
트리가 더러운 상태). 사용자 확인 후 vault 변경만 `50d672b`로 정리 커밋해 가드를 정당하게 통과시킨 뒤 진행.
vault 밖 pptx 변경은 건드리지 않았다.

표면화한 열린 질문 4건 — 재직 시기·기간 부재, 역할 수준·팀 규모 불명, vault에 넣은 목적 불명,
현 소속 여부 미확인.
