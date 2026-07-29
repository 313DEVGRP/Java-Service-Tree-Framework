---
type: source
created: 2026-07-29
updated: 2026-07-29
sources: [raw/2026-07-29-multiagent-subagent-audit-2026-07-29.md]
aliases: [멀티에이전트 점검 2026-07-29]
---

# 멀티에이전트 + 서브에이전트 시스템 점검 (2026-07-29)

[[java-service-tree-framework]]에 설치된 [[multiagent-orchestration-system]](flavor: claude)의 전면 점검 기록.

## 요약

시스템에 내장된 자가점검 [[system-invariants]](INV1–INV12) bash 블록을 직접 실행했다. 문서 요약이 아닌 실측이며 **핵심 항목 전부 PASS**.

INV5와 flavor 교차점검(INV12e/f)은 유지보수자 전용이고, 외부 매뉴얼과 generator templates가 이 설치본에 없어 스크립트가 정상적으로 건너뛴다 — 공개 설치본에서는 그게 정상이다. 루트의 `Multi_Sub_Agent_USE_Manual.pptx`는 INV5가 대조하는 `multi-agent-manual.txt`가 아니라 대조 대상이 아니다.

## 핵심 takeaway

가장 중요한 발견은 구조적인 것 — [[agent-layer-separation]]. `.claude/agents/` 한 폴더에 승인 게이트 대상인 [[worker-pool]]과 게이트 밖 [[domain-subagent]]가 공존하며, 둘을 혼동하면 시스템 규약이 무너진다.

슬롯 배정은 [[capability-slot]] 정본 5개 파일에서 상호 일치 확인:
strategist=claude-main · engineer/computer-use=codex-main · reviewer=codex-critic(주)+ollama(보조) · multimodal=gemini.

실행 환경: 워커 CLI 4개(`codex` `agy` `ollama` `python3`) 전부 PATH resolve. 디스패처 방어장치는 [[worker-dispatcher]] 참조.

작업 폴더 3건 모두 `status: done`, `workers/<role>/brief.md` 구조 준수, 납작한 `<role>_brief.md` 위반 0건.

## 관찰 — 계층 경계의 실전 처리

`landing-calendar-*` 두 작업에서 frontend-expert(도메인 서브에이전트)가 `workers/` 아래 폴더를 갖는다. 위반이 아니다 — task.md에 "게이트 대상이 아니나 실제 호출이 발생하므로 투명성 위해 기록"이라 명시돼 있다.

여기서 나오는 일반 원리: **승인 게이트 대상 여부**와 **산출물 기록 위치**는 별개 축이다. 게이트 밖 에이전트도 호출 사실은 기록하는 것이 이 시스템의 실전 관행이다. Producer-Reviewer 토폴로지에서 reviewer 자리에 codex-critic 대신 도메인 서브에이전트를 넣은 사례이기도 하다.

## 열린 질문

- 도메인 서브에이전트 산출물을 `workers/` 아래 두는 관행을 규약(CLAUDE.md·task-folder.md)에 명문화할지, 관행으로 남길지.
- INV 목록에 도메인 서브에이전트 관련 불변식이 없다. 두 계층 혼입(게이트 밖 에이전트가 `backends.json`에 등록되는 사고)을 막는 기계 검사를 추가할지.
