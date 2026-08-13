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

## [2026-08-13] ingest — 이동민 첫 소속 정정 (Daum → Daum Soft)

계기: query "이동민" 응답 후 사용자가 첫 소속 표기를 **Daum Soft**로 정정.

갱신한 페이지 (2): `leedongmin`(표 1행), `leedongmin-career`(요약 1줄 + 정정 경위 문단). 둘 다 `updated: 2026-08-13`.
`index.md` 2줄 갱신(요약 표기 + updated).

`raw/2026-07-30-leedongmin.md`는 **수정하지 않았다** — schema §구조와 소유권에 따라 raw/는 내용 불변이고
에이전트는 읽기 전용. 따라서 원자료("Daum")와 wiki("Daum Soft") 표기가 의도적으로 불일치하며,
`leedongmin-career`에 이 정정이 우선한다고 명기해 뒀다.
