---
type: concept
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [도메인 서브에이전트, 2계층]
---

# 도메인 서브에이전트

[[multiagent-orchestration-system]]의 ②계층 — 저장소를 **실제 개발할 때** 쓰는 도메인 특화 에이전트. 일반 Claude Code 서브에이전트로 동작하며 [[worker-pool]]과 별개 계층이다([[agent-layer-separation]]).

## 구성원 (2026-07-29 확인)

| 파일 | 도메인 |
|---|---|
| `frontend-expert.md` | vanilla JS · jQuery · Bootstrap 서버렌더링 프론트엔드 |
| `backend-expert.md` | Backend-Core(Spring Boot 2.6 · TreeFramework · Feign · Kafka · POI) + Auto-Code 생성기(Telosys Velocity) |

## ①계층과 다른 점

- 오케스트레이션 워커 규약(무통신·file-as-memory·헤드리스)을 **따르지 않는다**
- 직접 파일을 쓰고, 필요하면 사용자에게 질문한다 — one-shot 헤드리스가 아니므로 질문 채널이 있다
- `workers_approved` 승인 게이트 대상이 아니다
- `backends.json`에 등록하지 않는다
- [[capability-slot]]에 배정되지 않는다 — 도메인 전문성은 슬롯이 아니다

## 추가 방법

`.claude/agents/README.md` 표에 한 줄 추가 + `.claude/agents/<name>.md` 배치. 정본 5개(Worker Pool 문서)는 건드리지 않는다.

## 산출물 기록

게이트 밖이지만 실제 호출이 발생하면 `tasks/<task>/workers/<role>/`에 기록하는 것이 실전 관행이다. 게이트 대상 여부와 기록 위치는 별개 축 — 자세한 논거는 [[agent-layer-separation]].

## 관련

- [[multiagent-subagent-audit-2026-07-29]] — frontend-expert의 `workers/` 배치가 위반이 아님을 확인
