# 알려진 이슈

해결되지 않은 알려진 결함을 추적한다. 고쳐지면 해당 항목을 닫고(✅) PR 링크를 단다.
시스템이 깨지는 크리티컬은 즉시 수정 대상, 표시·미관 한정은 보류 가능.

출처: `repo-consistency-audit` (2026-05-19, claude-main·codex-main 병렬 + Orchestrator 교차검증).
상세 근거표(`repo-consistency-audit`)는 공개 배포본에 미포함 — 유지보수자 전용.

---

## ✅ KI-1 (audit C3) — 표준 `worker-brief.md`를 쓰면 mat이 워커 목적을 ` ```yaml `로 표시

- **상태**: **닫힘** (2026-08-24) — 1.1.0의 「Worker 행동 규약」 블록 삽입으로 **부수 해소**. 전용 수정 PR 없음
- **심각도**: 낮음 (해소 전 기준) — 시스템·워커 호출·데이터에 영향 없었음. [mat](https://github.com/netwaif/mat) 모니터 화면 표시만 오염
- **재현**: 현재 템플릿에서 **재현 불가** (아래 §해소 근거)

### 증상

mat의 핵심 화면 요소인 "워커 한 줄 목적"이 실제 Objective가 아니라 문자열 ` ```yaml `로 표시된다.

### 근본 원인

| repo | 파일·라인 | 내용 |
|------|-----------|------|
| starter | `_templates/worker-brief.md` **(해소 전 구조)** | 1행 `# Brief`(heading), 2–4행 `<!-- -->`(comment), 6행 `## Execution Context`(heading), **8행 ` ```yaml ` fence** |
| mat | `internal/parser/task.go:280` | brief 존재 시 무조건 `w.Purpose = firstMeaningfulLine(brief 내용)` |
| mat | `internal/parser/task.go:499–515` | `firstMeaningfulLine`은 **빈 줄·`#`시작·`<!--`시작만 skip**, 그 다음 줄을 그대로 반환 |
| mat | `internal/parser/task.go:71–76` | `w.Purpose == ""`일 때만 `planned_workers.purpose`로 fallback |

표준 brief에서 heading·comment를 건너뛴 첫 "의미 있는" 줄은 `## Execution Context` 다음의 ` ```yaml ` fence다. 이 값이 비어있지 않으므로 `planned_workers.purpose` fallback도 발동하지 않는다.

### 해소 근거 (2026-08-24 실측)

1.1.0에서 `_templates/worker-brief.md` **6행에 「## Worker 행동 규약」 섹션이 삽입**되면서,
heading·comment 다음의 첫 의미 있는 줄이 yaml fence가 아니라 규약 첫 항목이 됐다.
수정 후보 (a)(템플릿 재구성)·(b)(mat 파서)는 **둘 다 불필요** — 어느 쪽도 채택하지 않았다.

| 항목 | KI-1 기재 (해소 전) | 현재 실측 |
|------|--------------------|----------|
| `worker-brief.md` 6행 | `## Execution Context` | `## Worker 행동 규약 (고정 …)` |
| `worker-brief.md` 8행 | ` ```yaml ` fence | `- 요청 범위만 최소로. …` |
| `firstMeaningfulLine` 반환값 | ` ```yaml ` | `- 요청 범위만 최소로. 사변적 추상화·기능 추가 금지` |

검증: `internal/parser/task.go:499–516`의 skip 규칙(빈 줄·`#`·`<!--`)을 현재 템플릿에 재현 → fence 미도달.
mat 파서(`task.go:280`·`499`)는 **수정하지 않았다** — 임의 brief에 대한 견고성 개선 여지는 남아 있으나,
표준 템플릿에서는 증상이 발생하지 않으므로 이 이슈로 추적하지 않는다.

> 잔존 사항(이슈 아님): 표시되는 값이 Objective가 아니라 규약 첫 줄이다. mat 화면상
> 모든 워커가 동일 문자열을 보이므로 목적 구분에는 기여하지 않는다. 개선하려면 수정 후보 (b)
> 또는 `planned_workers.purpose` 우선 처리가 필요하다.

### 참고

- 공개 흔적: `_shared/learnings.md` [2026-05-19] (곁다리 언급), PR #5 본문.
- 크리티컬 해소 이력: PR #3 (C1 gemini 기본 모델), PR #5 (C2 gemini 단일 브리지).
