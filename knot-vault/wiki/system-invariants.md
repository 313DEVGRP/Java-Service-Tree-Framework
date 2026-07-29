---
type: concept
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [불변식, INV, 자가점검]
---

# System Invariants (자가점검)

[[multiagent-orchestration-system]]이 자기 모순을 기계적으로 잡는 장치. `_shared/system-invariants.md`에 불변식 목록(INV1–INV12)과 실행 가능한 bash 블록이 함께 들어 있다.

**핵심 발상** — 시스템 파일을 수정한 뒤 전면 멀티에이전트 재감사를 돌리는 대신 이 점검만 실행한다. 통과해야 커밋한다. 깨지면 고치거나, 의도된 변경이면 `design-basis.md`의 결정(D*)과 불변식 표를 **함께** 갱신한다.

평소에는 로드하지 않는다 — 시스템 파일 수정·검증 작업일 때만.

## 검사하는 것들

주로 **같은 사실이 여러 파일에 병기됐을 때의 불일치**를 잡는다.

- INV1 — `write_scope` 값 집합(`none`/`tasks-only`/패턴)이 4개 파일에서 동일
- INV3 — log 태그 정확히 6종 (`DECISION|WORKER_CALL|VERIFICATION|ERROR|APPROVAL|COMPLETE`)
- INV4 — context 1500자 / brief 1200자 한도 수치 일치
- INV7 — 권위 우선순위 문구 일치
- INV9/INV10 — gemini 백엔드가 `agy` CLI이고, 폐기된 프록시 브리지(`mcp__gemini__*`·`mcp__gemini-pro__*`)가 **활성 호출로** 남아 있지 않음
- INV11 — 재진입 프로토콜 존재, 토폴로지 4패턴 존재, 배제 패턴(Supervisor·Hierarchical) 부활 금지
- INV12 — 카파시 4원칙의 층별 적용. 특히 워커 규약 블록 안에 **사용자 질문 지시가 없어야** 한다 (워커는 one-shot이라 질문 채널이 없음)

INV10b는 흥미로운 형태다 — 문자열의 **존재 여부**가 아니라 그것이 '폐기 안내 문맥'인지 '활성 호출'인지를 판정한다. 기계 검사로 완전 자동화가 안 되고 사람 판단이 남는 지점.

## 유지보수자 전용 항목

INV5와 flavor 교차점검(INV12e/f)은 외부 매뉴얼 repo·generator templates가 있을 때만 실행된다. 공개 설치본에는 없으므로 스크립트가 건너뛰는 게 **정상 동작**이며 FAIL이 아니다.

## 이 점검으로 부족한 경우

새 외부 개념 도입, [[worker-pool]] 구성·역할 변경, 불변식으로 표현 불가한 구조 변경 → 그때만 새 작업 폴더 + codex-critic/gemini 전면 재감사.

## 알려진 공백

[[agent-layer-separation]]을 검사하는 불변식이 없다. ②계층([[domain-subagent]])이 `backends.json`에 잘못 등록되는 혼입 사고를 잡을 기계 검사가 부재하다.

## 관련

- [[multiagent-subagent-audit-2026-07-29]] — INV1–12 실행, 핵심 전항목 PASS
