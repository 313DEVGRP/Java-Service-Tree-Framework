# mat — MVP Design

## 목적

[multi-agent-starter](https://github.com/netwaif/multi-agent-starter) 시스템의
한 작업 진행 상황을 터미널에서 간결하게 모니터링한다.

MVP는 **모니터링만**. 작업 생성/승인/호출은 범위 밖.

## MVP 기능

### 포함

| 화면 요소 | 데이터 소스 | 방법 |
|---------|-----------|------|
| 작업 status / goal | `tasks/<task>/task.md` | YAML 헤더 파싱 |
| 워커 목록 | `tasks/<task>/workers/*/` 스캔 | 디렉토리 ls |
| 각 워커 상태 (대기·실행 중·완료·에러) | brief.md / result.md / log.md | 파일 stat + 태그 파싱 |
| 각 워커가 무엇을 하는지 | brief.md 첫 줄 또는 `purpose` 필드 | 텍스트 추출 |
| result.md 경로·크기 | `workers/<role>/result.md` | 파일 stat |
| log.md 동적 줄 수 (메인 뷰) | `tasks/<task>/log.md` | 터미널 높이에 맞춰 표시, 최소 5줄 |
| log.md 전체 (모달) | `L` 키 → 풀스크린 모달 | `j/k` 스크롤, `g/G` 처음·끝, `esc` 닫기. 모달 열린 동안 자동 reload 생략 |
| 작업 전환 | `tasks/` 폴더 스캔 | 디렉토리 ls |
| 자동 새로고침 | 2초 주기 폴링 | `tea.Tick` + 파일 다시 읽기 |
| 즉시 새로고침 | `r` 키 | 폴링 안 기다리고 바로 재로드 |
| 종료 | `q` 키 | exit |

### 제외 (불완전·버그 소지)

- 실시간 파일 watch (fsnotify) — OS별 동작 차이, 에디터 임시파일 노이즈 (대안으로 폴링 채택)
- log.md 실시간 tail 스트림 — 파일 watch 의존
- 산출물 폴더 실시간 변화 추적 — 같은 이유
- result.md 마크다운 렌더링 — TUI에서 까다로움. MVP는 경로·크기만
- 작업 생성·승인·워커 호출 — MVP는 모니터링만
- Discord/푸시 알림 — 별도 단계
- 다중 작업 동시 모니터링 — 한 작업 집중. 작업 전환만 지원

## 상태 아이콘

우선순위 高→低: 에러 → 재호출(log) → 완료 → 실행 중 → 대기.

| 아이콘 | 의미 | 판정 기준 |
|--------|------|---------|
| `[ ✗ ]` | 에러 | log.md의 해당 워커 마지막 언급이 `[ERROR]` |
| `[ ⏳ ]` | 실행 중 | (a) `brief*` 존재 + 비어있지 않은 짝 `result*` 없음, (b) 최신 brief 반복(`-fix<N>`)에 짝 result 반복이 아직 없음, 또는 (c) log.md에서 해당 워커 마지막 언급이 명백한 재호출(`재호출`·`재오픈`·`fix iter`·`N차`)이고 그 뒤 완료 기록 없음 |
| `[ ✓ ]` | 완료 | 비어있지 않은 result(또는 폴백 아티팩트)가 존재하고 그 반복번호 ≥ 최신 brief 반복번호 |
| `[ · ]` | 대기 | `brief` 없음 (task.md의 planned_workers엔 명시) |

**반복(fix-iter) 파일.** 워커는 `brief.md`→`brief-fix.md`→`brief-fix2.md`,
`result.md`→`result-fix.md`→`result-fix2.md`로 반복한다. brief/result는 각각 반복번호
우선(동률 시 mtime→이름)으로 1개 선택해 표시한다. 반복번호가 권위 신호(mtime은
git checkout·복사로 역전 가능). `result.partial-*`는 표시/완료에 미사용(UpdatedAt
신선도에만). `UpdatedAt`은 워커 폴더의 모든 `brief*`/`result*`(partial 포함) 최신 mtime.

## 와이어프레임

```
┌──────────────────────────────────────────────────────────┐
│ mat — Task: mat-mvp                                      │
│ Status: waiting_codex-main   ·   Updated: 14:35          │
├──────────────────────────────────────────────────────────┤
│ Goal                                                     │
│   mat TUI 도구 MVP 만들기                                │
├──────────────────────────────────────────────────────────┤
│ Workers                                                  │
│                                                          │
│  [ ✓ ] claude-main                완료    14:30          │
│        설계 문서 작성                                    │
│        result.md: workers/claude-main/result.md (3.2KB)  │
│                                                          │
│  [ ⏳ ] codex-main                실행 중                 │
│        Go TUI 코드 작성 (target: ~/VSCodeWorkspace/mat)  │
│        brief.md: workers/codex-main/brief.md (980자)     │
│                                                          │
│  [ · ] codex-critic               대기                   │
│        실행 예정 (claude-main 산출물 검토)               │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ Recent log (last N of M)                                 │
│  [14:30] [VERIFICATION] claude-main 통과                 │
│  [14:31] [APPROVAL] codex-main 사용자 승인              │
│  [14:33] [APPROVAL] 외부 쓰기 승인. target=~/.../mat    │
│  [14:34] [WORKER_CALL] codex-main 호출. brief=980자     │
│  [14:35] [DECISION] image_gen 도구 사용                 │
│  …(터미널 높이에 맞춰 더 많은 줄 표시, 최소 5줄)         │
├──────────────────────────────────────────────────────────┤
│ 자동 갱신 2s · [r] 즉시   [t] 작업 전환   [L] 로그   [q] 종료 │
└──────────────────────────────────────────────────────────┘
```

## 작업 전환 (`t` 키) 동작

`t` 키를 누르면 `tasks/` 폴더의 작업 목록 모달.

```
┌─── Tasks (select with j/k, enter to open) ────────┐
│  → mat-mvp                  waiting_codex-main    │
│    blog-cards-mvp           done                  │
│    20260513-receipt-fix     in_progress           │
│                                                   │
│  [esc] 취소                                       │
└───────────────────────────────────────────────────┘
```

`enter`로 선택, `esc`로 취소.

## 로그 모달 (`L` 키) 동작

`L`(또는 `l`) 키를 누르면 `log.md` 전체를 풀스크린 모달로 본다.

```
╔════════════════════════════════════════════════════════════╗
║ Log  (j/k 스크롤, g/G 처음/끝, esc 닫기) · 42줄            ║
║                                                            ║
║  [14:30] [VERIFICATION] claude-main 통과                   ║
║  [14:31] [APPROVAL] codex-main 사용자 승인                 ║
║  …                                                         ║
║                                                            ║
║  17–35 / 42                                                ║
╚════════════════════════════════════════════════════════════╝
```

- 진입 시 최신 줄로 자동 스크롤 (`logScroll = maxLogScroll`)
- `j/k` 1줄 스크롤, `g/G` 처음·끝 점프, `esc`/`q` 닫기, `ctrl+c` 종료
- 모달 열린 동안은 자동 새로고침(2s tick)에서 reload 생략 — 스크롤 위치 보존
- 터미널 리사이즈 시 `logScroll`을 새 `maxLogScroll`로 clamp

## 기술 스택

- **언어**: Go
- **TUI**: [bubbletea](https://github.com/charmbracelet/bubbletea) + [lipgloss](https://github.com/charmbracelet/lipgloss)
- **배포**: 단일 바이너리 + Homebrew tap (`netwaif/homebrew-tap`)

## 입력·출력 계약

- **입력**: 환경변수 `MAT_ROOT` 또는 cwd가 `~/VSCodeWorkspace/MultiAgent` 같은 starter root
- **활성 작업 결정 순서**:
  1. 커맨드 인자 `mat <task-name>` 명시 시 그 작업
  2. 없으면 `task.md`의 status가 `in_progress`·`reviewing`·`waiting_*`인 작업 중 가장 최근 수정
  3. 없으면 작업 목록 모달부터 띄움

- **상태 색**: `done`=초록, `waiting_*`=주황, `in_progress`=강조, `reviewing`=마젠타,
  `pending`=회색, `unknown`=빨강.
- **task artifacts/**: `tasks/<task>/artifacts/`에 항목이 있으면 워커 박스 아래
  Artifacts 박스로 최상위 엔트리(파일=크기, 디렉터리=재귀 파일 수) 표시. 비어 있으면
  박스를 그리지 않는다(레이아웃 산술에서 제외).

## 폴더 구조 (구현 시)

```
mat/
├── main.go               # 엔트리포인트
├── go.mod
├── internal/
│   ├── model/            # task/worker/log 데이터 모델
│   ├── parser/           # task.md, brief.md, log.md 파싱
│   └── ui/               # bubbletea View/Update
├── README.md
├── DESIGN.md             # 이 문서
└── .gitignore
```
