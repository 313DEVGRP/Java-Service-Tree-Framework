# `.claude/agents/` — 두 계층의 서브에이전트

이 폴더에는 **목적이 다른 두 계층**의 에이전트 정의가 공존한다. 등록·수정 시 계층을 반드시 구분할 것.

## 1. 오케스트레이션 Worker Pool

파일 기반 멀티에이전트 시스템의 정식 워커. **능력 슬롯에 배정**되며 슬롯 정의는 불변이다.
배정 정본은 `_shared/capability-profile.md`(가변층), 슬롯 정의는 `_shared/routing.md`(안정층).

| 파일 | name | 슬롯 |
|------|------|------|
| `claude-main.md` | `claude-main` | strategist |

> codex-main · codex-critic · gemini 는 `.claude/agents/` 파일이 아니라 MCP/CLI 로 호출된다
> (호출 스펙 정본: `_shared/backends.json`). Worker Pool 전체 목록은 `CLAUDE.md` Architecture 참조.

**이 계층에 워커를 추가하려면** `_shared/capability-profile.md` §갱신 절차를 따른다 —
새 능력 슬롯 판정 + 정본 5개(capability-profile · routing · CLAUDE.md · README · backends.json) 동기화.
도메인 전문성은 슬롯이 아니므로 이 계층에 넣지 않는다.

## 2. 도메인 서브에이전트 (Worker Pool과 별개 계층)

이 저장소(Java Service Tree Framework)를 **실제 개발할 때** 쓰는 도메인 특화 에이전트.
일반 Claude Code 서브에이전트로 동작한다 — 직접 파일을 쓰고, 필요 시 가정을 명시하거나 질문한다.
오케스트레이션 워커 규약(무통신·file-as-memory·헤드리스)을 따르지 않으며, `workers_approved`
승인 게이트 대상도 아니다. `backends.json` 에도 등록하지 않는다.

| 파일 | name | 도메인 |
|------|------|--------|
| `frontend-expert.md` | `frontend-expert` | vanilla JS · jQuery · Bootstrap 기반 서버렌더링 프론트엔드 |

**이 계층에 에이전트를 추가하려면** 이 표에 한 줄 추가하고 `.claude/agents/<name>.md` 를 둔다.
정본 5개(Worker Pool 문서)는 건드리지 않는다.
