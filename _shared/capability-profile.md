# Capability Profile — 슬롯 → 워커 배정 (가변층)

`routing.md`의 decision tree가 정하는 **능력 슬롯을 현재 어떤 워커가 맡는지**의 정본.
신모델 출시·판정 변경 시 **이 파일만 갱신**한다(근거·날짜 필수, 이력 append-only).
모델 식별자 자체의 표기·갱신은 `backends.json`·config 소관(design-basis D7) — 여기서는 배정만 다룬다.

## 현재 배정

| 슬롯 | 담당 워커 | 배정 근거 요약 |
|------|----------|--------------|
| strategist | claude-main (경량은 Orchestrator 직접) | 설계·UI/UX 디자인·전략·문체 우위 |
| engineer | — (Orchestrator 직접) | 전담 워커 없음. 구현·테스트·diff·로컬 검증은 Orchestrator 세션이 수행 |
| computer-use | — (Orchestrator 직접) | 전담 워커 없음. 브라우저·도구 워크플로우는 Orchestrator 세션 도구로 수행 |
| reviewer | claude-reviewer | 생성 모델(Opus 5.5)과 다른 모델(Sonnet 5.5)·깨끗한 컨텍스트의 독립 검증 (자기검수 회피) |
| multimodal | — (Orchestrator 직접) | 전담 워커 없음. 이미지·PDF·긴 문서는 Orchestrator 세션이 직접 읽음 |

> "—" 슬롯은 워커 호출이 아니라 Orchestrator 내부 작업이다 — `workers_approved` 승인 대상이 아니며,
> 외부 repo 수정 시 작업 `task.md` Constraints 에 write_scope 를 적고 `log.md` `[DECISION]` 에 남긴다.

## 배정 이력 (append-only)

- **2026-07-13** 초기 배정 + computer-use 슬롯 신설. 근거: 외부 리뷰 10건 종합 판정
  (Anthropic 최신 플래그십 vs OpenAI 최신 플래그십) — 디자인·전략·글쓰기 = Claude 우위,
  대규모 구현·테스트·브라우저 조작·비용·속도 = GPT 우위로 수렴. 요지는 design-basis D12.
- **2026-10-01** codex-main · codex-critic · gemini 워커 삭제, reviewer 슬롯에 `claude-reviewer`(model `claude-sonnet-5`) 신설.
  engineer · computer-use · multimodal 은 전담 워커 없이 Orchestrator 직접 수행. 근거: 사용자 지시(외부 벤더 워커 운용 중단).
  reviewer 독립성은 교차 벤더 → 교차 모델(생성 Opus · 검증 Sonnet 5) + 컨텍스트 격리로 대체. 요지는 design-basis D15.
- **2026-10-07** 모델 핀 갱신 — `claude-main` `opus` 별칭 → `claude-opus-5-5` 핀, `claude-reviewer` `claude-sonnet-5` → `claude-sonnet-5-5`.
  슬롯 배정 불변. 근거: 사용자 지시. 요지는 design-basis D16.

## 갱신 절차

1. 새 판정 자료 확보 (리뷰 종합 · 벤치마크 · 자체 실측)
2. 「현재 배정」 표 갱신 + 「배정 이력」에 날짜·근거 추가 (기존 이력 삭제 금지)
3. 담당명 병기 사본을 **전부** 이 표와 동기화 — `routing.md`(트리 · Worker 역할 상세의 슬롯 표기 · 최소 Worker Set), `CLAUDE.md`(Architecture 워커 풀), `README.md`(Workers 목록), `.claude/agents/claude-main.md` · `claude-reviewer.md`(description·역할). 병기는 편의 사본 — 슬롯 정의는 불변
4. 시스템 구조 파일(orchestrator-rules·invariants 등)은 손대지 않는다
