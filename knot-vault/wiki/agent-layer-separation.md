---
type: concept
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [두 계층 분리, 계층 구분]
---

# 에이전트 두 계층 분리

[[multiagent-orchestration-system]]에서 `.claude/agents/` **한 폴더에 목적이 다른 두 계층이 공존**한다는 원칙. 이 시스템에서 가장 혼동하기 쉬운 지점이며, 혼동하면 승인 게이트와 정본 동기화 규약이 동시에 무너진다.

| | ① [[worker-pool]] | ② [[domain-subagent]] |
|---|---|---|
| 목적 | 오케스트레이션 실행 | 저장소 실제 개발 |
| 구성원 | claude-main, codex-main, codex-critic, gemini, ollama | frontend-expert, backend-expert |
| 승인 게이트 | `workers_approved` 필수 | 대상 아님 |
| [[capability-slot]] | 배정됨 (정의 불변) | 없음 — 도메인 전문성은 슬롯이 아니다 |
| `backends.json` | 등록 | **등록 안 함** |
| 워커 행동 규약 | 준수 (무통신·file-as-memory·헤드리스) | 미준수 (직접 파일 쓰기, 질문 가능) |

## 추가 절차가 다르다

- ①에 추가 → `capability-profile.md` §갱신 절차. 새 능력 슬롯 판정 + **정본 5개 동기화**(capability-profile · routing · CLAUDE.md · README · backends.json)
- ②에 추가 → `.claude/agents/README.md` 표에 한 줄 + `<name>.md` 파일. **정본 5개는 건드리지 않는다**

도메인 전문성을 슬롯으로 착각해 ①에 넣는 것이 전형적 실수다.

## 파생 원리 — 게이트와 기록은 별개 축

**승인 게이트 대상 여부**와 **산출물 기록 위치**는 독립적이다. 게이트 밖(②) 에이전트도 실제 호출이 발생하면 `tasks/<task>/workers/<role>/`에 기록하는 것이 실전 관행이다 — 투명성 목적이며 규약 위반이 아니다.

`landing-calendar-*` 작업이 이 사례이고, Producer-Reviewer 토폴로지에서 reviewer 자리에 codex-critic 대신 ②계층을 넣은 예이기도 하다.

## 관련

- [[multiagent-subagent-audit-2026-07-29]] — 이 원칙을 실측 확인한 점검
- [[system-invariants]] — 단, 이 분리를 검사하는 불변식은 아직 없음
