package parser

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/netwaif/mat/internal/model"
)

const ymlFence = "```"

func writeFile(t *testing.T, path, body string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}

func writeTaskMD(t *testing.T, dir, status string, mtime time.Time) {
	t.Helper()
	md := filepath.Join(dir, "task.md")
	body := "# x\n\n## 메타\n\n" + ymlFence + "yaml\nstatus: " + status + "\n" + ymlFence + "\n"
	writeFile(t, md, body)
	if err := os.Chtimes(md, mtime, mtime); err != nil {
		t.Fatal(err)
	}
}

func TestBuildWorkerResultArtifactDetection(t *testing.T) {
	tests := []struct {
		name       string
		files      map[string]string
		wantState  model.WorkerState
		wantResult string
	}{
		{
			name: "result md wins",
			files: map[string]string{
				"brief.md":           "brief",
				"result.md":          "summary",
				"result.tokens.json": "[]",
			},
			wantState:  model.StateDone,
			wantResult: "result.md",
		},
		{
			name: "tokens artifact is done",
			files: map[string]string{
				"brief.md":           "brief",
				"result.tokens.json": "[]",
			},
			wantState:  model.StateDone,
			wantResult: "result.tokens.json",
		},
		{
			name: "output artifact is done",
			files: map[string]string{
				"brief.md":           "brief",
				"result.output.json": "{}",
			},
			wantState:  model.StateDone,
			wantResult: "result.output.json",
		},
		{
			name: "generic artifact is done",
			files: map[string]string{
				"brief.md":      "brief",
				"result.foo.md": "done",
			},
			wantState:  model.StateDone,
			wantResult: "result.foo.md",
		},
		{
			name: "partial only is running",
			files: map[string]string{
				"brief.md":                  "brief",
				"result.partial-05-11.json": "{}",
			},
			wantState: model.StateRunning,
		},
		{
			name: "brief only is running",
			files: map[string]string{
				"brief.md": "brief",
			},
			wantState: model.StateRunning,
		},
		{
			name: "empty result md does not complete",
			files: map[string]string{
				"brief.md":  "brief",
				"result.md": "",
			},
			wantState: model.StateRunning,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := t.TempDir()
			workersDir := filepath.Join(root, "workers")
			wdir := filepath.Join(workersDir, "gemini")
			if err := os.MkdirAll(wdir, 0o755); err != nil {
				t.Fatal(err)
			}
			logPath := filepath.Join(root, "log.md")
			if err := os.WriteFile(logPath, []byte(""), 0o644); err != nil {
				t.Fatal(err)
			}
			for name, body := range tt.files {
				if err := os.WriteFile(filepath.Join(wdir, name), []byte(body), 0o644); err != nil {
					t.Fatal(err)
				}
			}

			got := buildWorker(workersDir, "gemini", logPath)
			if got.State != tt.wantState {
				t.Fatalf("state = %v, want %v", got.State, tt.wantState)
			}
			if tt.wantResult == "" {
				if got.ResultPath != "" {
					t.Fatalf("result path = %q, want empty", got.ResultPath)
				}
				return
			}
			if filepath.Base(got.ResultPath) != tt.wantResult {
				t.Fatalf("result path = %q, want basename %q", got.ResultPath, tt.wantResult)
			}
			if got.ResultSize == 0 {
				t.Fatalf("result size should be non-zero")
			}
		})
	}
}

func TestRevision(t *testing.T) {
	cases := map[string]int{
		"result.md":                 0,
		"brief.md":                  0,
		"result-fix.md":             1,
		"brief-fix.md":              1,
		"result-fix2.md":            2,
		"brief-fix2.md":             2,
		"result.foo.md":             0,
		"result.tokens.json":        0,
		"result.partial-05-11.json": 0,
	}
	for name, want := range cases {
		if got := revision(name); got != want {
			t.Errorf("revision(%q) = %d, want %d", name, got, want)
		}
	}
}

// Pattern B: a newer brief revision exists but its paired result does not
// yet → the worker is re-running, not done.
func TestBuildWorkerRevisionPairing(t *testing.T) {
	root := t.TempDir()
	workersDir := filepath.Join(root, "workers")
	wdir := filepath.Join(workersDir, "claude-main")
	logPath := filepath.Join(root, "log.md")
	writeFile(t, logPath, "")

	writeFile(t, filepath.Join(wdir, "brief.md"), "b0")
	writeFile(t, filepath.Join(wdir, "result.md"), "r0 done")
	writeFile(t, filepath.Join(wdir, "brief-fix.md"), "b1")

	got := buildWorker(workersDir, "claude-main", logPath)
	if got.State != model.StateRunning {
		t.Fatalf("brief-fix without result-fix: state = %v, want StateRunning", got.State)
	}

	// fix iter completes → highest revision now has a result → done.
	writeFile(t, filepath.Join(wdir, "result-fix.md"), "r1 done")
	got = buildWorker(workersDir, "claude-main", logPath)
	if got.State != model.StateDone {
		t.Fatalf("result-fix present: state = %v, want StateDone", got.State)
	}
	if filepath.Base(got.ResultPath) != "result-fix.md" {
		t.Fatalf("result path = %q, want result-fix.md", got.ResultPath)
	}
	if filepath.Base(got.BriefPath) != "brief-fix.md" {
		t.Fatalf("brief path = %q, want brief-fix.md", got.BriefPath)
	}
}

// Pattern A: in-place re-run leaves the old result.md on disk; the only
// signal is log.md (real lines from MultiAgent/manual-final-review/gemini).
func TestBuildWorkerLogRerun(t *testing.T) {
	tests := []struct {
		name    string
		lastLog string
		want    model.WorkerState
	}{
		{
			name:    "recall dispatch in progress",
			lastLog: "[2026-05-15 20:09] [WORKER_CALL] gemini 2차 — mcp__gemini-pro__gemini_pro_prompt, model=gemini-3.1-pro-low. 성공",
			want:    model.StateRunning,
		},
		{
			name:    "recall decision reopen",
			lastLog: "[2026-05-15 20:08] [DECISION] 사용자 요청으로 작업 재오픈(status→in_progress). gemini를 pro-low로 재호출",
			want:    model.StateRunning,
		},
		{
			name:    "verification after recall is done",
			lastLog: "[2026-05-15 20:09] [VERIFICATION] gemini 2차 result 수신·검토",
			want:    model.StateDone,
		},
		{
			name:    "complete after recall is done",
			lastLog: "[2026-05-15 20:09] [COMPLETE] 2차 반영 완료. gemini result.md=pro-low로 대체",
			want:    model.StateDone,
		},
		{
			name:    "error wins",
			lastLog: "[2026-05-15 19:55] [ERROR] gemini 1차 호출 실패 — Proxy 400",
			want:    model.StateError,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			root := t.TempDir()
			workersDir := filepath.Join(root, "workers")
			wdir := filepath.Join(workersDir, "gemini")
			logPath := filepath.Join(root, "log.md")
			writeFile(t, filepath.Join(wdir, "brief.md"), "b")
			writeFile(t, filepath.Join(wdir, "result.md"), "first result")
			writeFile(t, logPath,
				"# Log\n\n[2026-05-15 19:48] [WORKER_CALL] gemini 호출. brief\n"+
					"[2026-05-15 19:56] [VERIFICATION] gemini result 수신\n"+
					tt.lastLog+"\n")

			got := buildWorker(workersDir, "gemini", logPath)
			if got.State != tt.want {
				t.Fatalf("state = %v, want %v", got.State, tt.want)
			}
		})
	}
}

func TestWorkerLogState(t *testing.T) {
	root := t.TempDir()
	logPath := filepath.Join(root, "log.md")
	writeFile(t, logPath,
		"[2026-05-15 19:48] [WORKER_CALL] gemini 호출\n"+
			"[2026-05-15 20:08] [DECISION] 작업 재오픈. gemini를 pro-low로 재호출\n")
	if s := workerLogState("gemini", logPath); s != logRerun {
		t.Fatalf("recall last line: got %v, want logRerun", s)
	}
	if s := workerLogState("codex-critic", logPath); s != logNone {
		t.Fatalf("role not mentioned: got %v, want logNone", s)
	}
	if s := workerLogState("gemini", filepath.Join(root, "missing.md")); s != logNone {
		t.Fatalf("missing log: got %v, want logNone", s)
	}
}

func TestPickActiveTaskReviewing(t *testing.T) {
	root := t.TempDir()
	tasksDir := filepath.Join(root, "tasks")
	base := time.Date(2026, 5, 16, 12, 0, 0, 0, time.UTC)
	mk := func(name, status string, ageMin int) {
		writeTaskMD(t, filepath.Join(tasksDir, name), status, base.Add(-time.Duration(ageMin)*time.Minute))
	}
	mk("p", "pending", 1)
	mk("d", "done", 2)
	mk("ip", "in_progress", 30)
	mk("wx", "waiting_codex-main", 40)
	mk("rv", "reviewing", 5) // newest qualifying

	if got := PickActiveTask(root); got != "rv" {
		t.Fatalf("PickActiveTask = %q, want \"rv\" (reviewing must be selectable & newest)", got)
	}
}

func TestReadArtifacts(t *testing.T) {
	t.Run("no artifacts dir", func(t *testing.T) {
		if a := readArtifacts(t.TempDir()); a != nil {
			t.Fatalf("got %v, want nil", a)
		}
	})
	t.Run("empty artifacts dir", func(t *testing.T) {
		td := t.TempDir()
		if err := os.MkdirAll(filepath.Join(td, "artifacts"), 0o755); err != nil {
			t.Fatal(err)
		}
		if a := readArtifacts(td); a != nil {
			t.Fatalf("got %v, want nil", a)
		}
	})
	t.Run("flat file and nested dir", func(t *testing.T) {
		td := t.TempDir()
		art := filepath.Join(td, "artifacts")
		writeFile(t, filepath.Join(art, "review-report.md"), "0123456789")
		writeFile(t, filepath.Join(art, "src", "a.go"), "x")
		writeFile(t, filepath.Join(art, "src", "sub", "b.go"), "y")

		got := readArtifacts(td)
		if len(got) != 2 {
			t.Fatalf("len = %d, want 2 (%v)", len(got), got)
		}
		byName := map[string]model.Artifact{}
		for _, a := range got {
			byName[a.Name] = a
		}
		f := byName["review-report.md"]
		if f.IsDir || f.Size != 10 {
			t.Fatalf("file entry = %+v, want size 10 not dir", f)
		}
		d := byName["src"]
		if !d.IsDir || d.Count != 2 {
			t.Fatalf("dir entry = %+v, want IsDir, Count 2", d)
		}
	})
}

func TestReadYAMLHeaderFrontmatterFallback(t *testing.T) {
	dir := t.TempDir()

	tests := []struct {
		name       string
		body       string
		wantStatus string
		wantOK     bool
	}{
		{
			name:       "frontmatter",
			body:       "---\nname: x\nstatus: done\n---\n\n## 과제\n본문\n",
			wantStatus: "done",
			wantOK:     true,
		},
		{
			name:       "fence wins over frontmatter",
			body:       "---\nstatus: frontmatter\n---\n\n## 메타\n\n```yaml\nstatus: fenced\n```\n",
			wantStatus: "fenced",
			wantOK:     true,
		},
		{
			name:   "unclosed frontmatter rejected",
			body:   "---\nstatus: done\n\n본문만 계속\n",
			wantOK: false,
		},
		{
			name:   "no header at all",
			body:   "# 제목\n\n본문\n",
			wantOK: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			md := filepath.Join(dir, tt.name+".md")
			writeFile(t, md, tt.body)
			hdr, ok := readYAMLHeader(md)
			if ok != tt.wantOK {
				t.Fatalf("ok = %v, want %v", ok, tt.wantOK)
			}
			if tt.wantOK && hdr["status"] != tt.wantStatus {
				t.Fatalf("status = %q, want %q", hdr["status"], tt.wantStatus)
			}
		})
	}
}
