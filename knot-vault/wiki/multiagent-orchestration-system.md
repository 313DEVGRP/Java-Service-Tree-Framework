---
type: entity
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [MultiAgent, 멀티에이전트 시스템]
---

# MultiAgent 오케스트레이션 시스템

파일시스템을 유일 인터페이스로 삼는 멀티에이전트 오케스트레이션 시스템. `multi-agent-starter` 스킬이 스캐폴딩하며 flavor 3종(claude·codex·antigravity)을 지원한다. [[java-service-tree-framework]]에는 claude flavor가 설치돼 있다.

## 구성

- Orchestrator — Claude Code 세션의 내부 추론. **워커가 아니다** → 승인·쿼터 대상 아님
- [[worker-pool]] — 외부 모델 호출. 전원 승인 게이트 대상
- [[domain-subagent]] — 저장소를 실제 개발할 때 쓰는 별개 계층

Orchestrator를 워커로 착각하는 것이 흔한 오해다. 반대로 claude-main은 같은 벤더라도 **별도 모델 호출**이므로 승인 대상이다.

## 정본 파일

| 파일 | 역할 | 층 |
|---|---|---|
| `CLAUDE.md` | 최상위 규약 (권위 1순위) | — |
| `_shared/routing.md` | 슬롯 정의·토폴로지 | 안정층 |
| `_shared/capability-profile.md` | [[capability-slot]] 배정 | 가변층 |
| `_shared/backends.json` | 워커 호출 스펙 | — |
| `_shared/system-invariants.md` | [[system-invariants]] 자가점검 | — |
| `_shared/design-basis.md` | 설계 결정(D*) 근거 | — |

권위 우선순위: `CLAUDE.md` > routing/approval/orchestrator-rules > 매뉴얼.

## 운영 특징

- **file-as-memory** — 워커 간 직접 통신 없음. 모든 상태가 `tasks/<task>/` 파일에
- **append-only log** — `log.md`는 수정·삭제 금지. 태그 6종 고정
- 작업 재개 시 Lifecycle 1번이 아니라 `orchestrator-rules.md` §3 재진입 프로토콜부터
- 채택 토폴로지 4종: Pipeline · Fan-out/Fan-in · Expert Pool · Producer-Reviewer (Supervisor·Hierarchical은 배제)

## 관련

- [[multiagent-subagent-audit-2026-07-29]] — 2026-07-29 전면 점검, INV 전항목 PASS
