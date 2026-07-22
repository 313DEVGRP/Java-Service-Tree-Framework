package model

import "time"

// WorkerState is one of the four DESIGN.md status icons.
type WorkerState int

const (
	StatePending WorkerState = iota // [ · ] brief 없음
	StateRunning                    // [ ⏳ ] brief 있고 짝 result 없음, 또는 log.md상 재호출 진행 중
	StateDone                       // [ ✓ ] 비어있지 않은 result(rev ≥ 최신 brief rev) 존재
	StateError                      // [ ✗ ] log.md의 해당 워커 마지막 언급이 [ERROR]
)

func (s WorkerState) Icon() string {
	switch s {
	case StateDone:
		return "[ ✓ ]"
	case StateRunning:
		return "[ ⏳ ]"
	case StateError:
		return "[ ✗ ]"
	default:
		return "[ · ]"
	}
}

func (s WorkerState) Label() string {
	switch s {
	case StateDone:
		return "완료"
	case StateRunning:
		return "실행 중"
	case StateError:
		return "에러"
	default:
		return "대기"
	}
}

// Worker holds everything the main view needs about one worker slot.
type Worker struct {
	Role        string
	State       WorkerState
	Purpose     string // brief 첫 줄 or planned purpose
	BriefPath   string
	BriefSize   int64 // bytes
	BriefChars  int   // rune count (한글 글자수)
	ResultPath  string
	ResultSize  int64
	UpdatedAt   time.Time // 가장 최근 파일의 mtime
	HasBrief    bool
	HasResult   bool
	FromPlanned bool // task.md planned_workers 에만 있고 디스크 dir 없음
}

// Artifact is one top-level entry under tasks/<name>/artifacts/.
type Artifact struct {
	Name  string
	Size  int64 // bytes (file); 0 for dir
	IsDir bool
	Count int // recursive file count (dir); 0 for file
}

// Task is the active task snapshot rendered by the main view.
type Task struct {
	Name       string
	Path       string // tasks/<name>/task.md
	Status     string
	Goal       string
	UpdatedAt  time.Time
	Workers    []Worker
	Artifacts  []Artifact // tasks/<name>/artifacts/ 최상위 (비면 nil)
	LogTail    []string   // 주석/빈 줄/헤딩 제외한 전체 로그 라인. UI가 잘라 표시한다.
	ParseError string     // 비어 있지 않으면 YAML 파싱 실패
}

// TaskBrief is one row of the task-switch modal.
type TaskBrief struct {
	Name      string
	Status    string
	UpdatedAt time.Time
}

// NilSnapshot is a sentinel zero value used by the UI when no task is loaded yet.
var NilSnapshot = Task{}
