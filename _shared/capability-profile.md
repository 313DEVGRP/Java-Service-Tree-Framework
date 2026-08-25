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
| reviewer | codex-critic (재활성 2026-08-25) | 교차 벤더 독립 검증 (자기검수 회피). ollama는 제거됨(2026-08-25). **가용 확인됨(2026-08-25 실측)**: `codex login` 완료(ChatGPT 인증)로 `mcp__codex__codex` 실호출 정상. 인증이 풀리면 `401 Unauthorized`로 실패하며 codex-main도 동일 영향 — 그 경우 검증은 Orchestrator 소스 실측에 의존하고 '제3자 독립 검증 미충족'을 각 작업에 명시한다 |
| multimodal | gemini | 멀티모달·대용량 문서 처리 |

## 배정 이력 (append-only)

- **2026-07-13** 초기 배정 + computer-use 슬롯 신설. 근거: 외부 리뷰 10건 종합 판정
  (Anthropic 최신 플래그십 vs OpenAI 최신 플래그십) — 디자인·전략·글쓰기 = Claude 우위,
  대규모 구현·테스트·브라우저 조작·비용·속도 = GPT 우위로 수렴. 요지는 design-basis D9.
- **2026-07-27** reviewer 슬롯에 ollama(자체호스팅 보조) 추가. 근거: 사용자 요청. 벤더 쿼터에
  묶이지 않는 독립 검증자 확보 — codex-critic 교차 다양성 보강. 기본 모델 gemma3
  (backends.json에서 교체 가능). 백엔드 = HTTP API(`adapters/ollama_api.sh`, 기본 호스트
  `http://<자체호스팅-호스트>:11434`, env `OLLAMA_HOST`로 재정의).
  주 검증자는 codex-critic 유지, ollama는 보조 — '검증 1회 원칙'은 슬롯 단위로 적용.
- **2026-07-28** 위 2026-07-27 항목의 사실 정정(배정 변경 아님). 도입 시 'localhost:11434
  로컬·오프라인'으로 기재했으나 어댑터 실제 기본값은 자체호스팅 **원격** 데몬이다.
  localhost는 무응답, 원격 호스트는 정상 응답(gemma3:latest 확인). 따라서 '쿼터 없음'은
  유효하나 '오프라인·네트워크 불필요'는 성립하지 않는다 — 네트워크 단절 시 이 슬롯은 사용 불가.
  routing.md · CLAUDE.md · README.md의 병기 사본도 동일하게 정정.

- **2026-08-25** reviewer 슬롯의 ollama **용도 한정**(배정 유지, 적용 범위 축소). 근거: 자체 실측.
  landing-function-license-flow 작업에서 12,688자 설계안 검증에 실패 — 요구 형식 8문항 중 **0건** 응답,
  점검 대상을 '완성된 리뷰'로 오인하고 칭찬·요약을 반환. 원인 규명을 위해 3단계 실험:
  (1) **모델 교체 무효** — qwen2.5:7b(7.6B, gemma3의 1.8배)로 동일 brief 재시도 → 역시 0/8.
      실패 양상만 바뀜(칭찬 → 재요약). 모델 용량 문제가 아님.
  (2) **분할 호출 부분 유효** — 8문항을 1문항씩 8회, 입력 190~604자로 축소 → 형식 준수 6/8로 개선.
      그러나 판정 정확도는 3/8. NO 3건이 전부 오답(Orchestrator 소스 대조로 확인)이고 근거 미제시.
      YES는 전부 정답, NO는 전부 오답 — **부정 판정을 신뢰할 수 없음**.
  (3) **길이가 진짜 원인** — 어댑터를 `/api/chat`으로 전환해 지시(system)와 대상(user)을 분리한 뒤
      대조 실험: 동일 system에서 user 219·500·1,500·4,000자는 8/8 형식 준수, user 11,585자는 0/8.
      즉 system 분리로는 상쇄되지 않으며 **user 페이로드 절대 길이**가 임계 요인이다.
  → 배정은 유지하되 **적용 범위를 축소**한다. 짧은 닫힌 체크리스트에는 형식 준수가 안정적이나,
    판정 정확도 한계(3/8)가 별도로 남으므로 **단독 수락 근거로 쓰지 말고 Orchestrator 실측을 병행**한다.
  어댑터 변경 동반: `adapters/ollama_api.sh` `/api/generate` → `/api/chat`,
  `<!-- SYSTEM -->…<!-- /SYSTEM -->` 마커로 system 분리(마커 없으면 전문 user — 하위호환 유지).

- **2026-08-25** reviewer 슬롯에서 **codex-critic 배정 해제**, 슬롯을 **공석**으로 둔다. 근거: 사용자 통보
  ("codex-critic은 사용할 수 없다"). 배정 해제만 수행하고 워커 정의·설계근거는 보존한다 —
  `backends.json` 레코드, `design-basis` D2(선행조건 일반화), `system-invariants` INV2,
  `_templates` 예시는 그대로 둔다. 존재하지 않는 워커를 가리키는 불변식이 생기면 자가점검이
  모순되므로, **정의는 남기고 배정만 뺀다**(가변층/안정층 분리 원칙).
  대체 배정 없음 — gemini 겸임도 하지 않는다(사용자 선택). 따라서 이 시점부터 **주 검증자가 없고**,
  산출물 수락 판정은 Orchestrator의 소스 직접 실측(never-trust-upstream)이 유일한 근거다.
  이는 '자기검수 회피' 원칙(design-basis Consensus 항)이 약해진 상태임을 의미하므로,
  검증 워커가 확보되면 우선 복구 대상이다.

- **2026-08-25** reviewer 슬롯에서 **ollama 완전 제거**(배정 해제가 아닌 워커 삭제). 근거: 사용자 지시.
  같은 날 용도 한정(4,000자 이하 체크리스트 전용)까지 했으나, 실측된 판정 정확도 3/8
  (부정 판정 3건 전부 오답)로 독립 검증자 가치가 없다고 판단됨. 제거 범위:
  `backends.json` 워커 레코드 · `adapters/ollama_api.sh` · 병기 사본 전체.
  codex-critic(정의 보존)과 달리 **완전 삭제**이므로 복구는 git 이력에서 되돌려야 한다.
  이로써 **reviewer 슬롯에 배정된 워커가 하나도 없다**(codex-critic 비활성 + ollama 제거).
  대체 배정 없음 — gemini 겸임도 하지 않는다(사용자 선택). 검증은 Orchestrator 소스 실측 단독.
  자기검수 회피 원칙(design-basis Consensus 항)이 성립하지 않는 상태이므로,
  검증 워커 확보는 시스템의 최우선 복구 대상이다.

- **2026-08-25** reviewer 슬롯에 **codex-critic 재활성**(사용자 지시). `backends.json`의
  `disabled`·`disabled_reason` 두 필드 제거 — 정의를 보존해 둔 덕에 배정 복구만으로 완료.
  **다만 실호출은 아직 불가**: MCP 도구 `mcp__codex__codex` 호출이 `401 Unauthorized`
  (`Missing bearer or basic authentication`)로 실패한다. 원인은 워커 설정이 아니라 **codex 인증 부재** —
  `~/.codex/auth.json` 없음, `OPENAI_API_KEY` 미설정. 같은 백엔드를 쓰는 **codex-main도 동일 영향**이다.
  → 시스템 설정상 차단은 해제됐고(`disabled` 제거 확인), 인증(`codex login` 또는 `OPENAI_API_KEY`)만
    갖추면 즉시 동작한다. 그전까지 reviewer 검증은 Orchestrator 소스 실측에 의존하며,
    각 작업 Acceptance Criteria에 '제3자 독립 검증 미충족'을 명시한다(은폐 금지).

- **2026-08-25** reviewer 슬롯 **가용 상태 정정**(배정 변경 아님 — 사실 정정). 위 재활성 항목은 실호출이
  `401 Unauthorized`로 불가하다고 기재했으나, 이후 `codex login`(ChatGPT 인증)이 완료되어
  `~/.codex/auth.json`이 존재하고 `mcp__codex__codex` 실호출이 정상 동작함을 실측 확인했다
  (스모크 3회 전부 `OK` 반환). codex-main도 동일하게 가용하다. **따라서 reviewer 슬롯은 현재 살아 있고**,
  '주 검증자 없음'을 전제로 한 서술(자기검수 회피 원칙 미성립)은 이 시점부터 해당하지 않는다.
  이력 삭제 없이 정정 항목만 추가하며, 「현재 배정」 표와 `routing.md`의 병기 경고 블록을 함께 갱신했다.
  단, 인증은 환경이 소유하는 사실이라 언제든 풀릴 수 있으므로 **조건형 서술로 바꿔** 유지한다
  (인증 없으면 401 → Orchestrator 소스 실측으로 대체). `OPENAI_API_KEY`는 여전히 미설정이나
  `auth.json`만으로 동작하므로 필수가 아니다.

## 갱신 절차

1. 새 판정 자료 확보 (리뷰 종합 · 벤치마크 · 자체 실측)
2. 「현재 배정」 표 갱신 + 「배정 이력」에 날짜·근거 추가 (기존 이력 삭제 금지)
3. 담당명 병기 사본을 **전부** 이 표와 동기화 — `routing.md`(트리 · Worker 역할 상세의 슬롯 표기 · 최소 Worker Set), `CLAUDE.md`(Architecture 워커 풀), `README.md`(Workers 목록), `.claude/agents/claude-main.md`(description·역할). 병기는 편의 사본 — 슬롯 정의는 불변
4. 시스템 구조 파일(orchestrator-rules·invariants 등)은 손대지 않는다
