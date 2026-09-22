---
description: 오케스트레이션 워커와 도메인 서브에이전트 목록을 정본 파일에서 유도해 보고한다 (가용성 실측 · 등록 정합성 검사 포함)
argument-hint: "[--no-probe] [--drift-only]"
allowed-tools: Read, Glob, Grep, Bash(ls:*), Bash(cat:*), Bash(which:*), Bash(jq:*), Bash(sed:*), Bash(grep:*), Bash(wc:*)
---

# Agent Check — 워커·서브에이전트 목록

이 저장소에서 **실제로 호출할 수 있는 에이전트**를 정본 파일에서 읽어 보고한다. 사용자 입력: `$ARGUMENTS`

읽기 전용이다. 파일을 쓰거나 고치지 않는다.

---

## 0. 원칙 — 목록을 이 파일에 적지 말 것

워커·서브에이전트 구성은 **바뀐다.** 생성기 재스캐폴딩(`multi-agent-starter`)이 시스템 파일을 템플릿으로
재생성하면 워커 풀 문서가 통째로 교체되고, 도메인 에이전트는 `.claude/agents/` 에 파일을 놓는 것만으로 늘어난다.
그래서 이 command 는 **매번 정본을 읽어 유도**한다. 캐시된 목록을 답하지 않는다.

정본 우선순위는 `_shared/design-basis.md` §2 를 따른다 — `CLAUDE.md` > `_shared/routing.md`·`approval-policy.md` > 그 외.
문서 간 값이 어긋나면 **높은 쪽을 답하고 어긋난 사실을 §4 에 보고**한다.

| 무엇 | 정본 |
|---|---|
| Tier 1 워커 풀 구성 | `CLAUDE.md` §Architecture |
| 능력 슬롯 → 워커 배정 | `_shared/capability-profile.md` §현재 배정 |
| 호출 스펙(call_type · model · sandbox) | `_shared/backends.json` |
| 라우팅 판단 규칙 | `_shared/routing.md` |
| 승인 대상 여부 | `_shared/approval-policy.md` |
| 도메인 서브에이전트 | `.claude/agents/*.md` (실물) + `.claude/agents/README.md` (표) |
| 짝 스킬 | `.claude/skills/*/SKILL.md` |
| 슬래시 커맨드 | `.claude/commands/*.md` |

---

## 1. 절차

### 1.1 Tier 1 — 오케스트레이션 워커

```bash
sed -n '/^## Architecture/,/^## 운영/p' CLAUDE.md
sed -n '/^## 현재 배정/,/^## /p' _shared/capability-profile.md
jq -r '.workers | to_entries[] | "\(.key)\t\(.value.call_type)\t\(.value.model)"' _shared/backends.json
```

워커마다 **슬롯 · 호출 방식 · 모델 · 파일 쓰기 권한**을 모은다.
쓰기 권한은 `CLAUDE.md` §Worker 파일 쓰기 정책 표에서 읽는다(추측하지 말 것).

### 1.2 도메인 서브에이전트

```bash
ls .claude/agents/
grep -E '^\| `' .claude/agents/README.md
```

각 `.md` 의 frontmatter `name` 과 `description` 을 정본으로 쓴다. `model:` 핀이 있는지도 본다
(없으면 **세션 모델 상속**이다 — 있는 것처럼 답하지 말 것).

`.claude/agents/README.md` 는 이들이 **오케스트레이션 워커 풀과 같은 계층인지 별개 계층인지**를 규정한다.
그 서술을 그대로 반영한다 — 승인 게이트 대상인지, `backends.json` 등록 대상인지가 여기서 갈린다.

### 1.3 가용성 실측 (`--no-probe` 면 생략)

목록에 있는 것과 **지금 호출되는 것은 다르다.** 반드시 실측해서 함께 보고한다.

```bash
which codex agy 2>&1 | tail -2
```

- **codex MCP**: 세션에 `mcp__codex__*` 도구가 로드돼 있는지로 판정한다. 세션 시작 시 연결 실패가 보고됐으면
  그 사실을 쓴다. **연결 실패를 "미설정"·"기능 없음" 으로 단정하지 말 것** — 서버 문제일 수 있으니
  "연결 실패라 사용자가 재시도·복구해야 한다" 로 보고한다.
- **CLI 폴백**: `codex` 가 PATH 에 없으면 MCP 실패 시 폴백도 불가하다(`routing.md` codex-main §MCP 실패 시 폴백).
- **gemini**: `agy` 가 PATH 에 없으면 호출 경로가 없다. `backends.json` 의 `gemini.fallbacks` 가 빈 배열이면
  폴백도 없다(D11 — 미구현 슬롯 비활성). **쿼터를 쓰는 스모크 호출은 기본으로 하지 않는다.**
  사용자가 명시적으로 요청할 때만 `routing.md` 가 권하는 경량 스모크 1회를 제안한다.
- **claude-main·도메인 서브에이전트**: Task tool 경유라 세션 내에서 항상 호출 가능하다.

### 1.4 호스트 기본 제공 에이전트

`.claude/agents/` 에 없는데 세션에서 호출 가능한 것들(`general-purpose` · `Explore` · `Plan` 등)은
**프로젝트 정의가 아니라 Claude Code 제공**이다. 별도 블록으로 구분해 적고,
`workers_approved` 승인 게이트 대상이 아님을 명시한다. 이 목록은 세션에서 확인되는 것만 쓴다.

### 1.5 등록 정합성 검사 (drift)

이 command 의 "check" 가 이것이다. 아래를 대조해 **어긋난 것만** 보고한다.

```
① .claude/agents/*.md 실물  ↔  .claude/agents/README.md 표     (표에 없는 파일 / 파일 없는 표 행)
② .claude/agents/*.md 실물  ↔  backends.json workers 키         (등록 여부 — README 의 계층 규정과 일치해야)
③ capability-profile 배정   ↔  CLAUDE.md §Architecture 병기     (프로필이 정본. 어긋나면 프로필이 이긴다)
④ capability-profile 배정   ↔  routing.md 트리 병기             (같음)
⑤ 각 에이전트의 짝 스킬      ↔  .claude/skills/ 실물            (README 가 "상세 규약은 X 스킬" 이라 적은 경우)
```

드리프트가 0 이면 "정합성 이상 없음" 한 줄로 끝낸다. 있으면 무엇이 어느 파일에서 어떻게 다른지 적고,
**고치지는 않는다** — 이 command 는 읽기 전용이다. 수정이 필요하면 별도 작업으로 안내한다.

`--drift-only` 면 §1.5 결과만 출력하고 목록은 생략한다.

---

## 2. 보고 형식 (한국어)

```
## Tier 1 — 오케스트레이션 워커 (승인 필요)
표: 워커 | 능력 슬롯 | 호출 방식 | 모델 | 파일 쓰기 | 가용성
→ 실제로 호출 가능한 워커가 몇 개인지 한 줄로 요약

## 도메인 서브에이전트
표: 이름 | 담당 모듈·도메인 | 짝 스킬
→ .claude/agents/README.md 가 규정한 계층(워커 풀과 동일/별개)과 승인 대상 여부를 한 줄로

## 호스트 기본 제공 (프로젝트 정의 아님)
나열 + 승인 게이트 비대상 명시

## 부수 자산
슬래시 커맨드 · 스킬 개수와 목록

## 정합성
이상 없음 / 또는 드리프트 목록
```

가용성이 목록과 다르면 그게 가장 중요한 정보다 — **표 안에 묻지 말고 요약 한 줄로 따로 말한다.**

---

## 3. Do NOT

- 목록·배정을 이 파일이나 기억에서 답하기 (항상 정본 파일을 읽는다)
- 파일 수정·생성, 드리프트 자동 교정
- 쿼터를 소모하는 워커 호출(gemini 스모크 포함)을 사용자 요청 없이 실행
- MCP 연결 실패를 "해당 기능 없음"·"미설정" 으로 단정
- `model:` 핀이 없는 에이전트에 특정 모델을 단정해서 적기
- 도메인 서브에이전트를 능력 슬롯에 배정된 것처럼 적기 (`.claude/agents/README.md` 의 계층 규정을 따른다)

---

## 4. 사용 예

```
/agent-check                # 전체 목록 + 가용성 실측 + 정합성
/agent-check --no-probe     # 목록·정합성만 (PATH·MCP 실측 생략)
/agent-check --drift-only   # 등록 정합성 검사 결과만
```
