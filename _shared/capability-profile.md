# Capability Profile — 슬롯 → 워커 배정 (가변층)

`routing.md`의 decision tree가 정하는 **능력 슬롯을 현재 어떤 워커가 맡는지**의 정본.
신모델 출시·판정 변경 시 **이 파일만 갱신**한다(근거·날짜 필수, 이력 append-only).
모델 식별자 자체의 표기·갱신은 `backends.json`·config 소관(design-basis D7) — 여기서는 배정만 다룬다.

## 현재 배정

| 슬롯 | 담당 워커 | 배정 근거 요약 |
|------|----------|--------------|
| strategist | claude-main (경량은 Orchestrator 직접) | 설계·UI/UX 디자인·전략·문체 우위 |
| engineer | codex-main | 대규모 구현·테스트 철저, 비용·속도·토큰 효율 우위 |
| computer-use | codex-main | 브라우저 조작·복잡 워크플로우 수행 우위 |
| reviewer | codex-critic (주) · ollama (자체호스팅 보조) | 교차 벤더 독립 검증 (자기검수 회피). ollama는 자체호스팅 Ollama 기반 보조 검증자 (쿼터 없음, 네트워크 의존) |
| multimodal | gemini | 멀티모달·대용량 문서 처리 |

## 배정 이력 (append-only)

- **2026-07-13** 초기 배정 + computer-use 슬롯 신설. 근거: 외부 리뷰 10건 종합 판정
  (Anthropic 최신 플래그십 vs OpenAI 최신 플래그십) — 디자인·전략·글쓰기 = Claude 우위,
  대규모 구현·테스트·브라우저 조작·비용·속도 = GPT 우위로 수렴. 요지는 design-basis D9.
- **2026-07-27** reviewer 슬롯에 ollama(자체호스팅 보조) 추가. 근거: 사용자 요청. 벤더 쿼터에
  묶이지 않는 독립 검증자 확보 — codex-critic 교차 다양성 보강. 기본 모델 gemma3
  (backends.json에서 교체 가능). 백엔드 = HTTP API(`adapters/ollama_api.sh`, 기본 호스트
  `http://mad.hyper-mig.com:11434`, env `OLLAMA_HOST`로 재정의).
  주 검증자는 codex-critic 유지, ollama는 보조 — '검증 1회 원칙'은 슬롯 단위로 적용.
- **2026-07-28** 위 2026-07-27 항목의 사실 정정(배정 변경 아님). 도입 시 'localhost:11434
  로컬·오프라인'으로 기재했으나 어댑터 실제 기본값은 자체호스팅 **원격** 데몬이다.
  localhost는 무응답, 원격 호스트는 정상 응답(gemma3:latest 확인). 따라서 '쿼터 없음'은
  유효하나 '오프라인·네트워크 불필요'는 성립하지 않는다 — 네트워크 단절 시 이 슬롯은 사용 불가.
  routing.md · CLAUDE.md · README.md의 병기 사본도 동일하게 정정.

## 갱신 절차

1. 새 판정 자료 확보 (리뷰 종합 · 벤치마크 · 자체 실측)
2. 「현재 배정」 표 갱신 + 「배정 이력」에 날짜·근거 추가 (기존 이력 삭제 금지)
3. 담당명 병기 사본을 **전부** 이 표와 동기화 — `routing.md`(트리 · Worker 역할 상세의 슬롯 표기 · 최소 Worker Set), `CLAUDE.md`(Architecture 워커 풀), `README.md`(Workers 목록), `.claude/agents/claude-main.md`(description·역할). 병기는 편의 사본 — 슬롯 정의는 불변
4. 시스템 구조 파일(orchestrator-rules·invariants 등)은 손대지 않는다
