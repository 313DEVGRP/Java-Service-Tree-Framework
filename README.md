# MultiAgent — Claude · Codex · Gemini Orchestration Starter

Claude Code를 오케스트레이터로 두고 Claude·Codex·Gemini를 워커로 호출하는 **파일 기반 멀티에이전트 시스템**.

## 핵심 아이디어

- **Orchestrator = Claude Code 세션** (이 폴더 안에서 실행 시 `CLAUDE.md` 자동 적용)
- **Workers** = 외부 모델 호출. 모두 승인 게이트 통과 필요.
  - `claude-main` — [strategist] 기획·설계·아키텍처·전략·디자인 방향·문체 글쓰기
  - `codex-main` — [engineer·computer-use] 대규모 구현·테스트·로컬 검증·브라우저 자동화·이미지 생성
  - `codex-critic` — [reviewer] 산출물 리뷰·비평 (Codex의 주된 역할)
  - `gemini` — [multimodal] 이미지·긴 문서·제3자 시각의 검토

  슬롯→워커 배정의 정본은 `_shared/capability-profile.md`(가변층) — 신모델 출시 시 프로필만 갱신.
- **Memory = filesystem.** 런타임 상태 없음. 모든 결정·승인·검증이 파일로 남는다.

## 폴더 구조

```
<설치한-폴더>/
├── CLAUDE.md              # 운영 규칙 전문 (이 폴더 안에서 claude 실행 시만 적용)
├── .claude/agents/        # ①워커 풀 정의 + ②도메인 서브에이전트 (계층 구분: 같은 폴더 README)
├── _shared/
│   ├── routing.md             # 능력 슬롯 decision tree + worker 역할 상세 (안정층)
│   ├── capability-profile.md  # 슬롯 → 워커 배정 정본 (가변층, 이력 append-only)
│   ├── backends.json          # worker 호출 스펙 정본 (call_type·모델·폴백·timeout)
│   ├── approval-policy.md     # 승인 게이트 정책 (claude-main 포함)
│   ├── orchestrator-rules.md  # 세션 시작 시 자체 점검 + §3 작업 재진입 프로토콜
│   ├── design-basis.md        # 설계 결정 기록 (D1~D9) — 왜 이 규칙인지
│   ├── system-invariants.md   # INV1~12 자가점검 (시스템 파일 수정 후 실행)
│   ├── learnings.md           # 시스템 일반 재사용 교훈 (추적·공개, append-only)
│   └── adapters/              # 디스패처 call_worker.sh + cli·api 어댑터
├── _templates/
│   ├── task.md            # status, goal, constraints, planned_workers, workers_approved
│   ├── context.md         # 현재 스냅샷 ≤ 1500자 / 300단어
│   ├── worker-brief.md    # ≤ 1200자 / 240단어, target_repo + write_scope
│   ├── worker-result.md   # Verification Checklist 포함
│   ├── log.md             # append-only 이력
│   └── task-folder.md     # 새 작업 폴더 생성 가이드
└── tasks/                 # 작업별 폴더 (동적 생성)
    └── <task-name>/
        ├── task.md
        ├── context.md
        ├── log.md
        ├── sources/       # 원본 자료 (선택)
        ├── workers/<role>/
        │   ├── brief.md
        │   └── result.md
        └── artifacts/     # 산출물 원본 (선택)
```

> `_local/` (git 추적 안 함, clone 시 빈 폴더): 작성자의 **프로젝트 특화** 교훈
> (`_local/learnings.md`)이 여기 쌓인다. 공개 starter에는 **시스템 일반** 교훈만
> `_shared/learnings.md`로 배포된다. 분류 규칙은 `_shared/learnings.md` 헤더 참조.

## 사용 시작

```bash
cd <설치한-폴더>
claude
```

자연어로 새 작업 요청:
> "새 작업 만들어줘. 목표는 ○○이고 ○○ worker가 필요할 것 같아."

Orchestrator가 `_templates/task-folder.md` 가이드에 따라 작업 폴더 생성 → worker 승인 요청 → 진행.

## 모니터링 (선택) — mat

작업 진행을 터미널에서 지켜보고 싶다면 **[mat](https://github.com/netwaif/mat)** (MultiAgent Tracker)를 함께 쓴다.
한 작업의 워커 상태(대기·실행 중·완료·에러)·goal·로그를 한 화면에서 본다.
시스템을 **읽기만** 한다 — 작업 생성·승인·워커 호출은 하지 않으므로, 켜두거나 꺼도 진행에 영향이 없다.

```bash
brew install netwaif/tap/mat
MAT_ROOT=<설치한-폴더> mat
```

설치·키 조작 등 자세한 내용은 [mat 저장소](https://github.com/netwaif/mat) 참고.

## 알려진 이슈

알려진 결함(해결·보류)은 [`KNOWN_ISSUES.md`](./KNOWN_ISSUES.md)에 추적한다. 현재 열린 이슈 없음 (KI-1 닫힘, 2026-08-24).

## 핵심 원칙

| 원칙 | 강제 방식 |
|------|---------|
| 모든 worker 호출 전 승인 | `task.md`의 `workers_approved` 필드 |
| 측정 가능한 컨텍스트 한도 | `wc -m` / `wc -w`로 검증 |
| append-only 로그 | `log.md` 수정·삭제 금지 |
| 최소 worker set | `routing.md` decision tree로 강제 |
| codex-main 외부 repo 쓰기 4-조건 | `target_repo` + `write_scope` + 승인 + log [APPROVAL] |

자세한 규칙은 [`CLAUDE.md`](./CLAUDE.md) 참고.

## 라이선스
개인 사용 및 학습 목적.

# 마법의 4줄
요구사항정의서_엑셀양식_v3_1_3.xlsx 의 {REQ-AIAGENT-DEV-02} 요구사항을 기준으로
요구사항_TASK_전환_Format.md
요구사항_TASK_전환_Sample.md
두개의 md 파일을 참고하여 작업을 만들고
만들어진 작업을 진행해 줘. 
승인이나 결정이 필요한 내용은 나에게 물어보지 말고 우선 진행을 하고,
로그에 임의 결정한 사항을 정리해서 남겨줘
( 엑셀 시트가 업데이트 되었으니까, 작업을 업데이트하고 진행 해 )

# 마법의 4줄

요구사항정의서_엑셀양식_v3_1_3.xlsx 의 REQ-AIAGENT-DEV-02 요구사항을 기준으로
tasks/요구사항_TASK_전환_Format.md
tasks/요구사항_TASK_전환_Sample.md
두개의 md 파일을 참고하여 작업을 만들어줘.

# mat 환경 변수
go build -o mat.exe .
$env:MAT_ROOT = "C:\~~~\Java-Service-Tree-Framework-main"

# worker 구성
[Worker Settings]
- MainWorker            : claude-main
- SubWorker             : 없음 (ollama 삭제, 대체 SubWorker 미배정)
- MainWorker-SubAgent   : reviewer-agent (신규)
  ※ 본 작업 자체는 reviewer-agent 로 검증할 수 없다 (자기검수 · 대상이 리뷰어 자신).
  Orchestrator 소스 실측 + 자가 점검 스크립트로 대체한다.

# 사용 예시
claude 와 인터렉션은 powershell 을 따로 띄워서 진행한다. ( 여러작업을 진행할 수 있고, 스크롤 이슈를 해결한다. )
mat 는 인텔리제이 아래 terminal 에서 진행한다.
1. 워커와 서브에이전트 목록을 알려줘
2. Task 목록을 깨끗하게 정리해 줘 ( 전체 비우기, 규칙문서도 삭제 )

요구사항정의서_엑셀양식_v3_1_3.xlsx 의 {REQ-AIAGENT-DEV-02} 요구사항을 기준으로
( Project Charter, SRS )를 기준으로 작성된 작업을 진행해 줘