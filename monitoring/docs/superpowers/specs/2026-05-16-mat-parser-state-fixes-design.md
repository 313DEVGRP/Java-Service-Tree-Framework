# mat 재실행 상태 버그 + #1/#2/#4 — 설계 (2026-05-16, 개정 2)

## 0. 이 개정에서 바뀐 것

초안(개정 1)은 #1/#2/#3을 다뤘으나 **사용자가 보고한 실제 버그(worker 중지→재실행 시
상태 표시가 갱신 안 됨)를 다루지 않았다.** 사용자/codex 합의 항목도 #1·#2·**#4**(개정 1의
#3 아님 — #3은 codex 판정 PARTIAL + 실효성 낮음: 실제 result.md 대부분 `status:` 필드
없음)로 정정됐다. 본 개정의 범위:

- **R — 재실행 상태 버그 (최우선, 사용자 보고 버그).** 패턴 A·B 둘 다.
- **#1 — 수정 반복 파일 인식.** R(패턴 B)의 *수단*이라 자동 포함.
- **#2 — `reviewing`/`pending` 상태.**
- **#4 — task `artifacts/` 노출.**
- **제외: #3** (result yaml `status`). 실효성 낮음 — 별건.

**이 작업은 mat repo만 수정한다.** `~/VSCodeWorkspace/MultiAgent/` 아래는 한 글자도
쓰지 않는다. 조사도 전부 읽기 전용으로 수행했다(아래 증거).

## 1. 근본원인 (추측 아님 — 코드 + 실제 MultiAgent 데이터로 확정)

### 1.1 구조적 원인

`internal/parser/task.go:212-221` `buildWorker` 상태머신:

```go
switch {
case workerHasError(role, logPath): w.State = StateError
case w.HasResult:                    w.State = StateDone   // ← 영구 고착
case w.HasBrief:                     w.State = StateRunning
default:                             w.State = StatePending
}
```

상태가 **Done 방향으로 단조(monotonic)**. 비어있지 않은 result 파일이 한 번 디스크에
생기면, 그 role의 *최신* 로그 줄이 `[ERROR]`가 되는 경우를 제외하곤 **Done→Running
전이 경로가 코드에 존재하지 않는다.** worker를 중지→재실행해도 이전 실행의 result
파일이 폴더에 남아 `HasResult=true` → 계속 `StateDone`(`[ ✓ ] 완료`). 이것이 사용자
보고 버그의 근본원인.

### 1.2 실제 재실행 패턴 2가지 (`manual-final-review` 한 task 안에 둘 다 존재)

증거 — `MultiAgent/tasks/*` (읽기 전용 조사):

**패턴 B — fix-iter (새 파일 생성).**
`mat-log-improve/workers/claude-main`: `result.md`(2026-05-14 10:25:57) → 재호출 시
`brief-fix.md`(13:24:55) → `result-fix.md`(13:28:23) → `brief-fix2.md`(14:30:25) →
`result-fix2.md`(14:32:15). 원본 `result.md`는 안 지워짐. log.md:
`[13:25] [WORKER_CALL] claude-main 호출 (fix iter). brief: .../brief-fix.md` →
`[13:30] [WORKER_CALL] claude-main fix iter 응답 수령. result-fix.md 저장`.
`manual-final-review/workers/codex-critic`: `brief.md`(19:48:04)/`result.md`(19:55:23)
→ `brief-fix.md`(20:36:31)/`result-fix.md`(20:38:55).
→ **재실행 구간 [brief-fix mtime ~ result-fix mtime] 동안 현행 mat은 Done (버그).**
파일 신호 **존재**: 최신 brief revision이 짝 result revision보다 큼.

**패턴 A — in-place (제자리 덮어쓰기, 새 파일/새 brief 없음).**
`manual-final-review/workers/gemini`: `brief.md`(19:48:18) 불변, `result.md`만
20:09:11로 덮어써짐(1차 Flash ~19:56 → 2차 pro-low 20:09). log.md:
`[20:08] [DECISION] 사용자 요청으로 작업 재오픈(status→in_progress). gemini를 pro-low로
재호출` → `[20:09] [WORKER_CALL] gemini 2차 — ... 성공` → `[20:09] [COMPLETE] 2차 반영
완료. ... gemini result.md=pro-low로 대체`.
→ **재실행 구간 [~20:08 ~ 20:09:11] 동안 현행 mat은 Done (버그).**
파일 신호 **전혀 없음**(brief.mtime < result.mtime 그대로). 유일한 신호는 **log.md**.
design-basis.md §1: "Filesystem=오버플로 메모리, 런타임 상태 0 / log.md append-only
권위 활동원장 / mtime은 비신뢰(git checkout·복사로 역전 가능)". → 패턴 A는 log.md로만
판정 가능.

### 1.3 log.md 형식 (실측, `_templates/log.md` + 실제 task)

`[YYYY-MM-DD HH:MM] [TAG] 내용` — TAG 고정 enum
`DECISION | WORKER_CALL | VERIFICATION | ERROR | APPROVAL | COMPLETE`.
role 이름은 내용에 자유 토큰으로 등장(`claude-main`/`gemini`/`codex-critic`).
**주의: `[WORKER_CALL]`은 과적재** — 호출(dispatch)·"응답 수령"·"파일 적용" 모두 같은
태그. `[COMPLETE]`는 task 레벨(보통 role 미명시). → 자유 텍스트 분류는 본질적으로
휴리스틱이므로 **degrade-safe(애매하면 기존 동작 유지)** 로 설계한다. (mat CLAUDE.md:
파서는 의도적으로 최소·"never panics, always degrades".)

## 2. 변경 파일 (격리 범위)

| 경로 | 변경 |
|---|---|
| `internal/parser/task.go` | `buildWorker` 재작성(revision 짝맞춤), `workerLogState` 신설(workerHasError 흡수+재호출 감지), `readArtifacts` 신설, `PickActiveTask` 술어 1줄 |
| `internal/model/types.go` | `Task.Artifacts []Artifact` + `Artifact` 타입 신설, `WorkerState` doc 코멘트 갱신. enum 4종 **불변** |
| `internal/ui/view.go` | `statusStyle`에 `reviewing`/`pending` case + `colorReview`, artifacts 박스 렌더 + `renderMain` `usedRows` 산술에 조건부 포함 |
| `internal/parser/task_test.go` | `buildWorker` 테이블 확장 + `PickActiveTask`/`readArtifacts`/log-rerun 테스트 신규 |
| `DESIGN.md` | 상태판정·활성작업·반복파일·artifacts 규칙 패치 (CLAUDE.md상 spec of record) |

**무변경**: `internal/ui/model.go`(폴링·모달·레이아웃·overlay·truncate), `main.go`,
`internal/parser/yaml.go`. 외부 의존성 0 추가. `WorkerState` enum 4종 재사용.

## 3. 설계

### 3.1 워커 파일 분류 + revision (#1 / 패턴 B 수단)

워커 디렉터리(`workers/<role>/`) 파일 분류:

- **brief md** — `HasPrefix(name,"brief") && HasSuffix(name,".md")`
- **result md** — `HasPrefix(name,"result") && HasSuffix(name,".md")`
- **result 아티팩트** — 비-`.md` `result.*`, 단 `result.partial-*` **제외**
- **partial** — `result.partial-*` — UpdatedAt 신선도에만 사용

`revision(name)`: 확장자 제거 후 `-fix$`→1, `-fix<N>$`→N, 그 외 0. 정규식
`-fix(\d*)$`(확장자 제거 후), 매치 시 숫자 없으면 1.
예: `brief.md`/`result.md`→0, `*-fix.md`→1, `*-fix2.md`→2, `result.foo.md`→0.
**권위 신호는 revision**(mtime은 git checkout·복사로 비신뢰 — design-basis.md §1).

선택:
- `briefSel` = brief md 중 `(revision, mtime, name)` 사전식 최대. 비어있으면 무시.
  `HasBrief`/`BriefPath`/`BriefSize`/`BriefChars`/`Purpose` 채움(Purpose 폴백 기존 유지).
- `resultSel` = result md 중 `(revision, mtime, name)` 사전식 최대(비어있지 않은 것).
  없으면 아티팩트 폴백 — **기존 `bestResultFile` 우선순위 보존**:
  `result.tokens.json`→`result.output.json`→정렬된 generic non-partial 첫 비어있지 않은 것.
  채워지면 `HasResult`/`ResultPath`/`ResultSize`.
- `UpdatedAt` = `brief`/`result`로 시작하는 폴더 내 모든 파일(partial 포함) 최신 mtime.

### 3.2 재호출 로그 신호 (R / 패턴 A) — degrade-safe

`workerHasError`를 `workerLogState(role, logPath) -> {Error, ReRunning, None}` 로 확장
(기존 reverse-scan 구조·필터 그대로 — blank/`#`/`<!--` 제외, role 미언급 줄 skip):

role을 언급하는 **마지막** 로그 줄을 보고:
1. `[ERROR]` 포함 → `Error` (**기존 workerHasError 동작 완전 보존**).
2. 아니고, 그 줄이 *명백한 재-dispatch* 면 → `ReRunning`.
   - 재-dispatch 키워드(실측): `재호출` | `재오픈` | `fix iter` | `N차`(`\d차`) |
     (`호출` AND NOT 완료 키워드).
   - 완료 키워드: `응답 수령` | `수신` | `저장` | `완료` | `result` | `[COMPLETE]` |
     `[VERIFICATION]`.
   - 즉 마지막 role-언급 줄이 완료류면 `None`(→ 파일 기반 Done 유지).
3. 그 외 → `None`.

**안전 편향(사용자 명시 요구 "멀쩡한 거 깨지 말 것"):** `ReRunning`은 *명백한* 재호출
신호일 때만 Done→Running으로 뒤집는다. 애매 → `None` → 기존 파일 기반 동작. 즉
**거짓 Running(진짜 완료를 실행 중으로) 0 보장**, 거짓 음성(재실행 놓침)은 허용.
로그 없음/읽기 실패 → `None`(기존과 동일, no error state).

### 3.3 워커 상태 머신 (R+#1 통합, enum 4종 재사용)

우선순위 高→低:

1. `workerLogState == Error` → `StateError`  *(= 기존 동작)*
2. `workerLogState == ReRunning` → `StateRunning`  *(패턴 A 해결: in-place 재호출)*
3. `HasResult && resultSel.revision >= briefSel.revision` → `StateDone`
4. `HasResult && resultSel.revision <  briefSel.revision` → `StateRunning`
   *(패턴 B 해결: 최신 brief 반복에 짝 result 아직 없음)*
5. `HasResult`(brief 없음) → `StateDone`
6. `HasBrief` → `StateRunning`
7. 그 외 → `StatePending`

(briefSel 없으면 revision 0으로 본다 → 3번 `0>=0` Done, 기존과 동일.)

### 3.4 활성 작업 + 스타일 (#2)

- `PickActiveTask` 술어:
  `status=="in_progress" || status=="reviewing" || HasPrefix(status,"waiting_")`.
  최신 task.md mtime 동률처리 그대로. (재오픈 시 task가 `in_progress`로 가는 것은
  패턴 A 증거 log:24에서 확인 — 이미 커버됨. `reviewing`은 신규 커버.)
- `view.go`: `colorReview = lipgloss.Color("213")`(마젠타) 추가.
  `statusStyle`에 `case s=="reviewing":`→`colorReview`(Bold),
  `case s=="pending":`→`colorMuted`(명시화). 기존 case 불변.

### 3.5 task artifacts/ 노출 (#4)

신규 model 타입:

```go
type Artifact struct {
    Name  string // entry name (top-level of artifacts/)
    Size  int64  // 파일이면 바이트, 디렉터리면 0
    IsDir bool
    Count int    // 디렉터리면 재귀 파일 수, 파일이면 0
}
```
`Task.Artifacts []Artifact`.

`readArtifacts(taskDir)`: `tasks/<name>/artifacts/` 최상위 엔트리 나열. 디렉터리면
재귀 파일 수 count(저렴). ReadDir 실패/폴더 없음 → `nil`(never panic). 정렬:
디렉터리 우선 후 name.

`view.go`: `len(Task.Artifacts) > 0` 일 때만 `artifactsBox` 렌더 — 빈 경우(실측상
대다수) 박스 미표시. **레이아웃 산술 보존**: `parseErrBox`와 동일하게 `artifactsBox`도
조건부로 `usedRows += lipgloss.Height(artifactsBox) + 1` 에 포함(`renderMain`
133-139행 패턴). 박스 본문: `Artifacts` 타이틀 + 엔트리당 한 줄
(`name (12.3KB)` / `dir/ (N files)`), `truncate`로 셀폭 절단(기존 헬퍼 재사용).

### 3.6 데이터 흐름

기존 파이프라인 불변: `LoadTask` → 워커별 `buildWorker` + `readArtifacts` →
`model.Task` → UI. 폴링(2s tick)·모달·overlay·truncate·로그 동적높이 알고리즘
(artifacts 박스만 산술에 1행 추가) 손대지 않는다.

## 4. 엣지 케이스

- 첫 실행(재호출 무): log에 role 재-dispatch 줄 없음 → `None` → 파일 기반.
  brief만 → Running, result(rev≥brief) → Done. **기존 7 테스트 불변.**
- 패턴 B 진행 중: `brief-fix.md`(rev1) 있고 `result-fix.md` 아직 없음 →
  resultSel=result.md(rev0) < briefSel(rev1) → 규칙 4 → `StateRunning`. fix 완료
  후 result-fix.md(rev1) → 규칙 3 → `StateDone`.
- 패턴 A 진행 중: 마지막 gemini-언급 로그 줄 = `[WORKER_CALL] gemini 2차 ...`(완료
  키워드 없음) → `ReRunning` → 규칙 2 → `StateRunning`. 이후 `[COMPLETE]`/"result"
  포함 줄이 마지막 → `None` → 파일 기반 Done.
- partial-only(gemini 스트리밍): result 아님 → HasResult=false → brief 있으면
  Running. UpdatedAt만 신선.
- result가 JSON 아티팩트뿐(`result.tokens.json`만): result md 0개 → 아티팩트
  폴백 → HasResult, briefSel rev0, 규칙 3 → Done(기존 호환).
- log `[ERROR]`가 마지막 role 언급: 규칙 1 → Error(기존 완전 보존).
- artifacts/ 빈 폴더(실측 대다수): 박스 미표시, 레이아웃 불변.
- artifacts/ 중첩(`mat-mvp`: `internal/`,`fix/` 디렉터리 + `go.mod` 파일):
  최상위만 나열, 디렉터리는 `(N files)`. 깊은 트리뷰 안 함(읽기 전용 모니터 최소).

## 5. 테스트

**`task_test.go` 기존 7케이스 무변경 통과**(검증): 전부 -fix 파일 없음 + 빈 log →
`workerLogState=None`, briefSel rev0, 파일 기반 결과 = 기존과 동일.

**신규 `buildWorker`:**
- brief.md+result.md+brief-fix.md (result-fix 없음) → `StateRunning`(규칙 4).
- 위 + result-fix.md → `StateDone`, `ResultPath`=result-fix.md.
- brief.md+brief-fix2.md+result-fix2.md → `StateDone`, brief/result Path=*-fix2.
- log 마지막 줄 `[2026-05-15 20:09] [WORKER_CALL] gemini 2차 — 성공`, result.md
  존재 → `StateRunning`(규칙 2, 패턴 A).
- log 마지막 줄 `[20:09] [COMPLETE] ... gemini result.md=pro-low로 대체`, result.md
  존재 → `StateDone`(완료 키워드 → None → 파일 기반).
- log 마지막 줄 `[ERROR] gemini ...`, result.md 존재 → `StateError`(규칙 1 보존).
- 재호출 줄 뒤 완료 줄(`[WORKER_CALL] gemini 2차` → `[COMPLETE] ... gemini ...`)
  → `StateDone`(마지막 언급이 완료류).

**신규 `PickActiveTask`:** temp tasks에 pending/in_progress/reviewing/waiting_x/done
혼합 → 반환 ∈ {in_progress, reviewing, waiting_*} 중 최신 task.md mtime.

**신규 `readArtifacts`:** 빈 폴더→nil; 평면 파일(review-report.md)→1 Artifact
(IsDir=false,Size>0); 폴더 없음→nil; 중첩(파일+서브디렉터리)→최상위 엔트리,
디렉터리 Count=재귀 파일 수.

**수동:** `go build ./... && go vet ./... && go test ./...` 전부 green.
`MAT_ROOT=~/VSCodeWorkspace/MultiAgent ./mat manual-final-review`로 (이미 done이라
정적이지만) artifacts 박스에 review-report.md 표시, 워커 상태 회귀 없음 육안 확인.

## 6. DESIGN.md 패치 항목

- 상태 아이콘 표: `[ ✓ ]` 완료 = "선택된 result*.md(또는 폴백 아티팩트)가 비어있지
  않고 **그 revision ≥ 최신 brief revision**". `[ ⏳ ] 실행 중`에 추가:
  "(a) 최신 brief 반복에 짝 result 없음, 또는 (b) log.md에서 해당 role 마지막
  언급이 명백한 재호출(`재호출`/`재오픈`/`fix iter`/`N차`)이고 그 뒤 완료 기록
  없음". `[ ✗ ]` 에러는 기존 그대로(log 마지막 role 언급이 `[ERROR]`).
- 워커 파일: brief/result는 `*-fix*` 반복 중 revision 우선 선택. `UpdatedAt`은
  폴더 모든 brief*/result*(partial 포함) 최신 mtime.
- "활성 작업 결정 순서"에 `reviewing` 포함.
- 와이어프레임/포함표에 task `artifacts/` 박스 추가(비어있으면 미표시).
- 와이어프레임·기존 절·로그 모달 동작은 유지.

## 7. 미해결/주의

- log 재호출 감지는 휴리스틱(한국어 키워드). 안전 편향상 거짓 Running은 0이나
  거짓 음성(드문 표현의 재호출 놓침)은 가능 — 그 경우 패턴 B 파일 신호로 부분 보완.
- mtime 비신뢰 전제(design-basis.md §1) → 동률·역전 시 revision/name으로 결정론.
- `WorkerState` enum 4종 불변 — UI/아이콘/Label 회귀 위험 최소.
