# Log — wiki 동기화 SRS §10 선행 조사

<!-- append-only. 수정/삭제 금지. -->
<!-- 형식: [YYYY-MM-DD HH:MM] [TAG] 내용 -->
<!-- TAG: DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE -->

[2026-08-07 17:44] [DECISION] 신규 작업 생성 — tasks/wiki-sync-preflight/. 사용자가 분리를 명시 요청("§10 선행 조사도 task 만들어서 진행해줘")하여 orchestrator-rules §3 확인 절차 면제. 단 연결고리 3종은 면제 대상 아니므로 이행: ① task.md `parent: tasks/wiki-concurrent-edit-sync` ② context.md 필독 입력 경로 명시 ③ 메모리 인덱스 부모↔자식 포인터
[2026-08-07 17:44] [DECISION] 사전 정찰(Orchestrator 내부 추론, worker 아님) — routing.md 복합작업 우선순위 2 "worker 호출 전 자체 추론으로 해결 가능한지 먼저 판단" 적용. 5개 항목의 판정 가능성부터 분류
[2026-08-07 17:44] [VERIFICATION] §10-5 사전 정찰 — Broker-Hub Dockerfile·application-{live,stg,dev}.yml 확인. 설정이 config server(`global-config:33133`)로 외부화, 이 repo에 k8s 매니페스트·replicas·세션 어피니티 설정 없음. Middle-Proxy에도 nginx/upstream 설정 없음 → **코드 기반 판정 불가** 확정
