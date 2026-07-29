---
type: concept
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [능력 슬롯, capability profile]
---

# 능력 슬롯 (Capability Slot)

[[multiagent-orchestration-system]]이 **워커 선택을 모델명이 아니라 능력 단위로 추상화**하는 장치. 신모델이 나와도 배정 파일 한 곳만 갱신하면 되도록 안정층과 가변층을 분리한다.

- **슬롯 정의** = 안정층 `_shared/routing.md`. 불변
- **슬롯 → 워커 배정** = 가변층 `_shared/capability-profile.md`. 신모델 출시 시 여기만 갱신
- **모델 식별자 표기** = `backends.json` 소관 (design-basis D7)

## 슬롯 5종과 현재 배정 (2026-07-29 확인)

| 슬롯 | 담당 | 근거 요약 |
|---|---|---|
| strategist | claude-main (경량은 Orchestrator 직접) | 설계·UI/UX·전략·문체 우위 |
| engineer | codex-main | 대규모 구현·테스트, 비용·속도·토큰 효율 우위 |
| computer-use | codex-main | 브라우저 조작·복잡 워크플로우 우위 |
| reviewer | codex-critic (주) · ollama (보조) | 교차 벤더 독립 검증 (자기검수 회피) |
| multimodal | gemini | 멀티모달·대용량 문서 |

## 갱신 절차

1. 새 판정 자료 확보 (리뷰 종합·벤치마크·자체 실측)
2. 배정 표 갱신 + 배정 이력에 날짜·근거 append (기존 이력 삭제 금지)
3. 병기 사본 **전부** 동기화 — `routing.md` · `CLAUDE.md` · `README.md` · `.claude/agents/claude-main.md`
4. 시스템 구조 파일(orchestrator-rules·invariants)은 손대지 않는다

병기는 편의 사본일 뿐 슬롯 정의는 불변이다. 도메인 전문성은 슬롯이 아니므로 [[domain-subagent]]는 이 체계 밖이다.

## 이력이 남기는 교훈

배정 이력은 append-only이며 **사실 정정도 이력으로 남긴다**. 2026-07-28 항목은 ollama를 'localhost·오프라인'으로 잘못 기재한 것을 정정한 기록으로, 배정 변경이 아니다 — 실제 기본값은 원격 자체호스팅 데몬이었다.

## 관련

- [[worker-pool]] — 슬롯에 배정되는 워커 집합
- [[multiagent-subagent-audit-2026-07-29]] — 정본 5개 동기화 실측 확인
