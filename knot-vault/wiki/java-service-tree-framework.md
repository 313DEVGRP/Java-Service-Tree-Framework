---
type: entity
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [JSTF, A-RMS]
---

# Java Service Tree Framework

`C:\DEV\sourcecode\Java-Service-Tree-Framework` — 멀티 모듈 저장소. [[multiagent-orchestration-system]](claude flavor)이 설치돼 있고, 이 vault(`knot-vault/`)도 저장소 안에 함께 추적된다.

## 모듈 구성

| 모듈 | 역할 |
|---|---|
| Backend-Core | A-RMS 핵심 API 서버 — Spring Boot 2.6 · Java 11 · TreeFramework nested-set 트리 · JPA/MyBatis 혼용 · Feign(Engine-Fire) · Kafka · POI 리포트 |
| Auto-Code | Telosys Velocity 템플릿 기반 코드 생성기 |
| Frontend-Web | 서버렌더링 프론트엔드 |
| Engine-Fire | Backend-Core가 Feign으로 호출하는 엔진 |
| Broker-Hub · Middle-Proxy · Global-Config · IaC-System · AI | 그 외 모듈 |

Backend-Core와 Auto-Code는 `backend-expert`, Frontend-Web은 `frontend-expert`가 담당한다([[domain-subagent]]).

## 특기사항

- `CLAUDE.md`의 오케스트레이션 규칙은 **이 폴더 또는 하위에서 실행할 때만** 적용된다(의도된 격리). 전역 `~/.claude/CLAUDE.md`에 넣으면 다른 프로젝트로 규칙이 새어나간다
- `_local/learnings.md`는 git 추적 대상이 아니며 명시 요청 없이는 로드하지 않는다
- 시스템 운영 일반 교훈은 `_shared/learnings.md`(추적), 특정 외부 프로젝트 한정 교훈은 `_local/learnings.md`

## 관련

- [[multiagent-subagent-audit-2026-07-29]] — 설치된 오케스트레이션 시스템 점검
