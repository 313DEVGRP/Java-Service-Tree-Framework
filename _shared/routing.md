# Worker Routing Rules

## 2층 라우팅 — 안정층/가변층

이 파일의 decision tree는 **작업 유형 → 능력 슬롯**을 정한다(안정층 — 모델 세대가 바뀌어도 유효).
**슬롯 → 담당 워커 배정**의 정본은 `_shared/capability-profile.md`(가변층)다.
신모델 출시·판정 변경 시 **프로필만 갱신**한다 — 이 파일의 슬롯 정의는 손대지 않는다.
아래 트리의 워커명은 현 프로필 배정의 병기(편의 사본)다 — 프로필과 어긋나면 **프로필이 이긴다**.

## Decision Tree

```
작업 성격 파악 → 능력 슬롯 → 담당 워커 (배정 정본: capability-profile.md)
│
├── [strategist] 기획 · 설계 · 아키텍처 · 요구사항 · 전략 · UI/UX 디자인 방향
│   · 문체가 중요한 글쓰기 · 까다로운 로직 설계 · 디버깅 원인 분석?
│   └── claude-main
│
├── [engineer] 대규모 구현 · 리팩토링 · 테스트 작성·실행 · diff · 로컬 CLI 검증?
│   └── — (전담 워커 없음 → Orchestrator 직접)
│
├── [computer-use] 브라우저 조작 · 복잡한 도구 워크플로우 자동화?
│   └── — (전담 워커 없음 → Orchestrator 직접)
│
├── [reviewer] 산출물 리뷰 / 비판적 검증?
│   └── claude-reviewer   (Sonnet 5 · 읽기 전용)
│
├── [multimodal] 이미지 · 스크린샷 분석 / 50페이지+ 문서?
│   └── — (전담 워커 없음 → Orchestrator 직접)
│
└── 판단 어려움?
    └── claude-main으로 시작 후 필요 시 추가
```

## 복합 작업 우선순위

한 작업이 여러 분기에 해당할 때:

1. **선행 의존성 우선**: claude-reviewer는 리뷰 대상(보통 claude-main 결과 또는 Orchestrator 구현 diff)이 먼저 있어야 함 → 해당 산출물 뒤에 호출
2. **Orchestrator 내부 추론 우선**: 별도 worker 호출 전에 orchestrator 자체 추론으로 해결 가능한지 먼저 판단. 그래도 부족할 때만 claude-main 호출 (claude-main도 비용·쿼터 대상)
3. **검증은 한 번만**: claude-reviewer는 작업당 1회 원칙. 재호출은 검증 실패 시만
4. **전담 워커 없는 슬롯은 Orchestrator 직접**: engineer · computer-use · multimodal 은 워커를 만들어 부르지 않는다(승인 불요 · `[DECISION]` 기록)

## 토폴로지 패턴 (worker를 어떻게 엮을까)

decision tree로 "누구를" 고른 뒤, "어떻게 엮을지" 고른다. **단일 orchestrator 구조에 맞는 4패턴만** 쓴다.

| 패턴 | 언제 | 이 시스템에서 |
|------|------|-------------|
| Pipeline (순차) | 앞 결과가 뒤 입력 | 기본. claude-main → claude-reviewer → claude-main(반영) |
| Fan-out/Fan-in (병렬→통합) | 서로 독립된 산출물 여럿을 하나로 통합 | 예: claude-main(설계) ∥ claude-reviewer(기존 코드 리뷰). 각 brief에 "타 worker 결과 미참조" 명시. 통합은 아래 Fan-in 규칙 |
| Expert Pool (전문가 선택) | 작업 성격에 맞는 worker만 | 새 실행 패턴이 아니라 **worker 선택 정책** — 위 decision tree + 최소 worker set이 곧 이 패턴 |
| Producer-Reviewer (생성+게이트) | 산출물 품질 검증 필요 | claude-main 또는 Orchestrator(생성) → claude-reviewer(adversarial 게이트) |

**금지**: 같은 입력에 같은 종류 worker 동시 호출 (예: claude-main 2개).
**배제**: Supervisor(별도 long-lived 조정자 worker/런타임 동적분배 계층 추가)·Hierarchical Delegation(worker가 worker를 부르는 재귀 위임)은 단일 orchestrator·worker간 무통신·file-as-memory와 충돌 → 미사용. 근거: design-basis D6.

### Fan-in 규칙 (병렬 결과 통합)

병렬 worker 결과를 orchestrator가 하나로 합칠 때:
1. 각 worker 원문을 `result.md`에 그대로 보존 (요약본만 남기지 말 것 — telephone game 방지)
2. 결과가 충돌하면 삭제 금지 → 양쪽 출처 병기, 권위 우선순위/사실검증으로 해소, `log.md` [DECISION]에 근거 기록
3. 통합 결론 한 줄을 `context.md`에 기록

## Worker 역할 상세

### claude-main
- **슬롯**: strategist
- **용도**: 기획, 요구사항 정의, 설계 문서, 사용자 스토리, 아키텍처, 전략 수립, UI/UX 디자인 방향, 문체가 중요한 글쓰기, 까다로운 로직 설계, 디버깅 원인 분석, (설계와 분리 곤란한) 핵심 구현
- **결과물**: 코드 (구현·수정·diff), 설계 문서, 구조도, 의사결정 근거
- **호출 명령**: Claude Code 내장 **Task tool (sub-agent)**
  - `subagent_type`: `claude-main` (`.claude/agents/claude-main.md`에 정의)
  - `prompt`: brief.md 내용 그대로 전달
  - `model`: agent 정의 파일 frontmatter의 `model: opus`가 자동 적용 (별칭 — 현재 환경의 Opus로 해석. 버전 문자열 핀하지 않음. 모델 정책 참조)
  - `description`: 짧은 작업명 (3~5 단어)
- **권한**: 메인 Claude Code 세션의 권한 모드 상속. `--dangerously-skip-permissions` (yolo) 모드면 sub-agent도 yolo로 작동. 단 MultiAgent 시스템 게이트(`workers_approved`, 외부 쓰기 4조건)는 별개로 유지된다
- **비용**: 있음 (Opus(`opus` 별칭) sub-agent 호출. 별도 모델 호출이며 비용·쿼터 대상) → 승인 필요
- **파일 쓰기**: ❌ 직접 X. Task tool이 반환한 텍스트를 Orchestrator가 받아 `result.md`에 기록
- ※ Orchestrator의 내부 추론과 다름.

### claude-reviewer
- **슬롯**: reviewer
- **용도**: 리뷰 대상 산출물(주로 claude-main 코드·설계, Orchestrator 구현 diff, 또는 brief에 명시된 기존 코드·문서·소스)을 실제 repo/파일/CLI 관점에서 리뷰·비평. 실현 가능성, 비용, 테스트 커버리지, 사이드 이펙트 검토. 단순 확인용이 아닌 adversarial 비평
- **선행 조건**: 리뷰 대상 산출물 경로가 존재 — 보통 claude-main `result.md`, 또는 brief에 명시된 기존 코드·문서·소스
- **결과물**: 비평 리스트(심각도 순 · 근거 경로 · 수정 제안)
- **호출 명령**: Claude Code 내장 **Task tool (sub-agent)**
  - `subagent_type`: `claude-reviewer` (`.claude/agents/claude-reviewer.md`에 정의)
  - `prompt`: brief.md 내용 그대로 전달. brief에 "비평 모드" 명시, `target_repo` 명시(비평 대상 repo 컨텍스트), `write_scope: none`
  - `model`: agent frontmatter `model: claude-sonnet-5` 자동 적용 (사용자 지정 핀 — 모델 정책 참조)
  - `description`: 짧은 작업명 (3~5 단어)
- **brief 필수 필드** (`gate.sh` G5 가 읽는다):
  ```yaml
  target_repo: /absolute/path/to/repo                   # 비평 대상 절대 경로 (없으면 N/A)
  write_scope: none                                     # 값 집합 none | tasks-only | "src/**, tests/**" (CLAUDE.md 정의) — claude-reviewer 는 항상 none
  ```
- **읽기 전용 강제**: agent `tools` 화이트리스트 = `Read, Grep, Glob, Bash` (Write·Edit·NotebookEdit 없음). Bash 쓰기는 도구로 막히지 않으므로 `target_repo`가 git repo면 호출 전후 `scope_check.sh`(`write_scope=none`) 대조로 변경 0건 확인 (CLAUDE.md Task Lifecycle 6)
- **비용**: 있음 (Sonnet 5 sub-agent 호출. 별도 모델 호출이며 비용·쿼터 대상) → 승인 필요
- **파일 쓰기**: ❌ 직접 X. Orchestrator 경유
- **독립성**: 생성 쪽(Orchestrator · claude-main = Opus)과 다른 모델 + 깨끗한 컨텍스트. 교차 벤더 검증은 아님 — 같은 계열 편향이 우려되는 작업이면 사용자에게 외부 검토를 제안한다

### 폐기된 워커 (2026-10-01, design-basis D15)
- `codex-main` · `codex-critic`(`mcp__codex__codex`) · `gemini`(`agy` CLI · `call_worker.sh gemini`)는 **삭제**됐다. 활성 호출 경로로 쓰지 말 것. 옛 작업의 brief·result·log 에 남은 이름은 이력이다.

## 모델 정책

각 worker가 실제 어떤 모델로 도는지 정리. 사용자가 매번 명시할 필요는 없으며, 아래 기본이 자동 적용된다.

- **claude-main**: 별칭 **`opus`** (`.claude/agents/claude-main.md` frontmatter `model: opus`). 버전 문자열을 핀하지 않는다 — 별칭이 현재 환경의 최신 Opus로 자동 해석되므로 모델이 올라가도 갱신 불필요.
  - **추론 강도(effort)**: claude-main 정의엔 `effort` 필드가 **없음 → 세션 `/effort` 값을 상속**한다(현재 세션이 high면 high로 동작). 세션과 무관하게 고정하려면 frontmatter에 `effort: high` 등을 명시(상속 끔). 고정은 결정성↑이나 현재는 상속 유지가 기본.
- **claude-reviewer**: **`claude-sonnet-5` 핀** (`.claude/agents/claude-reviewer.md` frontmatter `model: claude-sonnet-5`, `backends.json` 동일 값). 사용자가 "Sonnet 5"를 지정했으므로 별칭(`sonnet`)이 아닌 버전 핀이다 — 별칭은 다음 Sonnet 세대로 자동 이동해 지정과 어긋날 수 있다(D7 예외, D15). 모델 변경은 두 파일을 함께 바꾼다.
  - **추론 강도(effort)**: claude-main과 같이 `effort` 필드 없음 → 세션 `/effort` 상속.

## 최소 Worker Set 원칙

| 작업 유형 | 권장 최소 set |
|----------|------------|
| 문서/기획/전략만 | claude-main |
| 설계 + 소규모 구현 | claude-main (설계·구현 일괄) |
| 대규모 구현·테스트 | claude-main (설계, 필요 시) → Orchestrator 직접 (구현·테스트) |
| 브라우저 자동화 | Orchestrator 직접 |
| 구현 + 비평 | 생성(Orchestrator 또는 claude-main) → claude-reviewer → 반영 |
| 이미지·대용량 문서 처리 | Orchestrator 직접 |
| 전체 검토 | claude-main → claude-reviewer |

모든 worker를 기본 호출하지 말 것. 필요한 worker만 선택.

## Worker 추가 조건

- 이미 있는 worker 결과로 해결 가능하면 추가 호출 금지
- 이전 결과가 검증 미통과 시에만 동일 worker 재호출 가능
