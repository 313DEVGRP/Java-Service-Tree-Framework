package parser

import (
	"bufio"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/netwaif/mat/internal/model"
)

// LoadTask reads tasks/<name>/{task.md,log.md,workers/*} and returns a Task
// snapshot. Never panics: parse failures degrade to status="unknown".
func LoadTask(root, name string) (model.Task, error) {
	taskDir := filepath.Join(root, "tasks", name)
	taskMD := filepath.Join(taskDir, "task.md")

	t := model.Task{
		Name: name,
		Path: taskMD,
	}

	st, err := os.Stat(taskMD)
	if err != nil {
		t.Status = "unknown"
		t.ParseError = "task.md not found"
		return t, err
	}
	t.UpdatedAt = st.ModTime()

	header, ok := readYAMLHeader(taskMD)
	if !ok {
		t.Status = "unknown"
		t.ParseError = "task.md YAML header missing or invalid"
	} else {
		t.Status = strings.TrimSpace(header["status"])
		if t.Status == "" {
			t.Status = "unknown"
		}
	}

	t.Goal = readGoal(taskMD)

	logPath := filepath.Join(taskDir, "log.md")
	// log lines (display only — UI slices to fit the available height
	// for the main view, or shows the full list in the log modal).
	t.LogTail = readLogLines(logPath)

	t.Artifacts = readArtifacts(taskDir)

	// workers
	planned := readPlannedWorkers(taskMD)
	workersDir := filepath.Join(taskDir, "workers")
	onDisk := map[string]bool{}

	entries, _ := os.ReadDir(workersDir)
	var diskWorkers []model.Worker
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		name := e.Name()
		onDisk[name] = true
		w := buildWorker(workersDir, name, logPath)
		// also fill purpose from planned if brief 첫 줄이 비었으면
		if w.Purpose == "" {
			for _, p := range planned {
				if p.Role == name {
					w.Purpose = p.Purpose
					break
				}
			}
		}
		diskWorkers = append(diskWorkers, w)
	}

	// planned-only (no dir): show as pending
	var plannedOnly []model.Worker
	for _, p := range planned {
		if onDisk[p.Role] {
			continue
		}
		plannedOnly = append(plannedOnly, model.Worker{
			Role:        p.Role,
			State:       model.StatePending,
			Purpose:     p.Purpose,
			FromPlanned: true,
		})
	}

	// stable order: planned order first, then disk-only sorted by name.
	order := map[string]int{}
	for i, p := range planned {
		order[p.Role] = i
	}
	all := append(diskWorkers, plannedOnly...)
	sort.SliceStable(all, func(i, j int) bool {
		oi, iok := order[all[i].Role]
		oj, jok := order[all[j].Role]
		switch {
		case iok && jok:
			return oi < oj
		case iok:
			return true
		case jok:
			return false
		default:
			return all[i].Role < all[j].Role
		}
	})
	t.Workers = all

	return t, nil
}

func readGoal(taskMD string) string {
	f, err := os.Open(taskMD)
	if err != nil {
		return ""
	}
	defer f.Close()

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	inGoal := false
	var lines []string
	for sc.Scan() {
		line := sc.Text()
		trim := strings.TrimSpace(line)
		if strings.HasPrefix(trim, "## ") {
			if inGoal {
				break
			}
			if strings.TrimSpace(strings.TrimPrefix(trim, "## ")) == "Goal" {
				inGoal = true
				continue
			}
		}
		if inGoal {
			if trim == "" && len(lines) == 0 {
				continue
			}
			lines = append(lines, line)
		}
	}
	// trim trailing blank lines
	for len(lines) > 0 && strings.TrimSpace(lines[len(lines)-1]) == "" {
		lines = lines[:len(lines)-1]
	}
	return strings.TrimSpace(strings.Join(lines, "\n"))
}

// readLogLines returns every non-blank, non-comment, non-heading line from
// log.md in chronological order. The UI is responsible for slicing (tail
// for the main view, full list for the log modal).
func readLogLines(path string) []string {
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	var kept []string
	for sc.Scan() {
		line := sc.Text()
		trim := strings.TrimSpace(line)
		if trim == "" {
			continue
		}
		if strings.HasPrefix(trim, "<!--") {
			continue
		}
		if strings.HasPrefix(trim, "#") {
			continue
		}
		kept = append(kept, trim)
	}
	return kept
}

var reFix = regexp.MustCompile(`-fix(\d*)$`)

// revision returns the fix-iteration number encoded in a worker file name:
// 0 for the original (brief.md / result.md / result.foo.md /
// result.tokens.json), 1 for "*-fix.md", N for "*-fix<N>.md". The trailing
// extension is stripped first. The revision — not mtime — is the
// authoritative freshness signal: git checkout / copy can invert mtimes.
func revision(name string) int {
	base := strings.TrimSuffix(name, filepath.Ext(name))
	m := reFix.FindStringSubmatch(base)
	if m == nil {
		return 0
	}
	if m[1] == "" {
		return 1
	}
	if n, err := strconv.Atoi(m[1]); err == nil {
		return n
	}
	return 1
}

type sel struct {
	path string
	size int64
	mod  time.Time
	rev  int
	ok   bool
}

// better reports whether c outranks best by (revision, mtime, name).
func better(c, best sel) bool {
	if !best.ok {
		return true
	}
	if c.rev != best.rev {
		return c.rev > best.rev
	}
	if !c.mod.Equal(best.mod) {
		return c.mod.After(best.mod)
	}
	return c.path > best.path
}

func buildWorker(workersDir, role, logPath string) model.Worker {
	w := model.Worker{Role: role}
	wdir := filepath.Join(workersDir, role)

	entries, _ := os.ReadDir(wdir)
	var briefSel, resultSel sel
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		st, err := os.Stat(filepath.Join(wdir, name))
		if err != nil || st.IsDir() {
			continue
		}
		// UpdatedAt = newest mtime of any brief*/result* file (incl partial).
		if (strings.HasPrefix(name, "brief") || strings.HasPrefix(name, "result")) &&
			st.ModTime().After(w.UpdatedAt) {
			w.UpdatedAt = st.ModTime()
		}
		c := sel{
			path: filepath.Join(wdir, name),
			size: st.Size(),
			mod:  st.ModTime(),
			rev:  revision(name),
			ok:   true,
		}
		isBrief := strings.HasPrefix(name, "brief") && strings.HasSuffix(name, ".md")
		isResultMD := strings.HasPrefix(name, "result") && strings.HasSuffix(name, ".md")
		isPartial := strings.HasPrefix(name, "result.partial-")
		switch {
		case isBrief:
			if better(c, briefSel) {
				briefSel = c
			}
		case isResultMD && !isPartial && st.Size() > 0:
			if better(c, resultSel) {
				resultSel = c
			}
		}
	}

	if briefSel.ok {
		w.HasBrief = true
		w.BriefPath = briefSel.path
		w.BriefSize = briefSel.size
		if data, err := os.ReadFile(briefSel.path); err == nil {
			w.BriefChars = utf8.RuneCountInString(string(data))
			w.Purpose = firstMeaningfulLine(string(data))
		}
	}

	if resultSel.ok {
		w.HasResult = true
		w.ResultPath = resultSel.path
		w.ResultSize = resultSel.size
	} else if rp, rs, rm, ok := bestResultFile(wdir); ok {
		// no result*.md — fall back to artifacts (tokens / output /
		// generic), preserving the original bestResultFile priority.
		w.HasResult = true
		w.ResultPath = rp
		w.ResultSize = rs
		resultSel = sel{path: rp, size: rs, mod: rm, rev: revision(filepath.Base(rp)), ok: true}
		if rm.After(w.UpdatedAt) {
			w.UpdatedAt = rm
		}
	}

	// state derivation, precedence high→low.
	switch ls := workerLogState(role, logPath); {
	case ls == logError:
		w.State = model.StateError
	case ls == logRerun:
		// log.md says this worker was re-dispatched with no later
		// completion → running again (covers in-place re-runs that leave
		// the old result.md on disk).
		w.State = model.StateRunning
	case w.HasResult && resultSel.rev >= briefSel.rev:
		w.State = model.StateDone
	case w.HasResult:
		// a newer brief revision exists but its paired result does not
		// (fix-iter restart in progress).
		w.State = model.StateRunning
	case w.HasBrief:
		w.State = model.StateRunning
	default:
		w.State = model.StatePending
	}
	return w
}

// readArtifacts lists the top-level entries of tasks/<name>/artifacts/.
// Missing / unreadable dir → nil (never panics). Dirs report a recursive
// file count; files report byte size. Sorted: dirs first, then name.
func readArtifacts(taskDir string) []model.Artifact {
	dir := filepath.Join(taskDir, "artifacts")
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	var out []model.Artifact
	for _, e := range entries {
		name := e.Name()
		if strings.HasPrefix(name, ".") {
			continue
		}
		if e.IsDir() {
			out = append(out, model.Artifact{
				Name:  name,
				IsDir: true,
				Count: countFiles(filepath.Join(dir, name)),
			})
			continue
		}
		st, err := e.Info()
		if err != nil {
			continue
		}
		out = append(out, model.Artifact{Name: name, Size: st.Size()})
	}
	if len(out) == 0 {
		return nil
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].IsDir != out[j].IsDir {
			return out[i].IsDir
		}
		return out[i].Name < out[j].Name
	})
	return out
}

func countFiles(root string) int {
	n := 0
	filepath.WalkDir(root, func(_ string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if !d.IsDir() {
			n++
		}
		return nil
	})
	return n
}

func bestResultFile(wdir string) (string, int64, time.Time, bool) {
	preferred := []string{"result.md", "result.tokens.json", "result.output.json"}
	for _, name := range preferred {
		path := filepath.Join(wdir, name)
		if st, ok := nonEmptyFile(path); ok {
			return path, st.Size(), st.ModTime(), true
		}
	}

	entries, err := os.ReadDir(wdir)
	if err != nil {
		return "", 0, time.Time{}, false
	}
	var candidates []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if !strings.HasPrefix(name, "result.") {
			continue
		}
		if strings.HasPrefix(name, "result.partial-") {
			continue
		}
		path := filepath.Join(wdir, name)
		if _, ok := nonEmptyFile(path); ok {
			candidates = append(candidates, path)
		}
	}
	sort.Strings(candidates)
	if len(candidates) == 0 {
		return "", 0, time.Time{}, false
	}
	st, ok := nonEmptyFile(candidates[0])
	if !ok {
		return "", 0, time.Time{}, false
	}
	return candidates[0], st.Size(), st.ModTime(), true
}

func nonEmptyFile(path string) (os.FileInfo, bool) {
	st, err := os.Stat(path)
	if err != nil || st.IsDir() || st.Size() == 0 {
		return nil, false
	}
	return st, true
}

type logState int

const (
	logNone logState = iota
	logRerun
	logError
)

var (
	reRerunNum = regexp.MustCompile(`\d+차`)
	completeKW = []string{"응답 수령", "수신", "저장", "[COMPLETE]", "[VERIFICATION]", "완료", "result"}
	rerunKW    = []string{"재호출", "재오픈", "fix iter"}
)

// workerLogState classifies the LATEST log.md line mentioning role (same
// scan/filters as readLogLines: blank / "#" / "<!--" excluded, reverse
// order). It absorbs the old workerHasError:
//
//   - line carries [ERROR]               → logError  (unchanged behavior)
//   - line is a clear re-dispatch with no
//     completion keyword                 → logRerun
//   - anything else / no mention / no log → logNone
//
// Safety bias: logRerun only fires on an unambiguous re-dispatch, so the
// caller never shows a genuinely-done worker as running; a missed re-run
// is acceptable (the file-based revision pairing still covers fix-iters).
func workerLogState(role, logPath string) logState {
	f, err := os.Open(logPath)
	if err != nil {
		return logNone
	}
	defer f.Close()

	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	var kept []string
	for sc.Scan() {
		trim := strings.TrimSpace(sc.Text())
		if trim == "" || strings.HasPrefix(trim, "<!--") || strings.HasPrefix(trim, "#") {
			continue
		}
		kept = append(kept, trim)
	}
	if sc.Err() != nil {
		return logNone
	}
	for i := len(kept) - 1; i >= 0; i-- {
		ln := kept[i]
		if !strings.Contains(ln, role) {
			continue
		}
		if strings.Contains(ln, "[ERROR]") {
			return logError
		}
		for _, kw := range completeKW {
			if strings.Contains(ln, kw) {
				return logNone
			}
		}
		for _, kw := range rerunKW {
			if strings.Contains(ln, kw) {
				return logRerun
			}
		}
		if reRerunNum.MatchString(ln) {
			return logRerun
		}
		return logNone
	}
	return logNone
}

func firstMeaningfulLine(s string) string {
	sc := bufio.NewScanner(strings.NewReader(s))
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "<!--") {
			continue
		}
		return line
	}
	return ""
}

// PickActiveTask implements DESIGN.md activation order:
//  1. (caller already handled arg)
//  2. task.md status==in_progress|reviewing|waiting_* — newest task.md mtime
//  3. "" — caller opens modal
func PickActiveTask(root string) string {
	tasksDir := filepath.Join(root, "tasks")
	entries, err := os.ReadDir(tasksDir)
	if err != nil {
		return ""
	}
	type cand struct {
		name string
		mt   time.Time
	}
	var cands []cand
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasPrefix(name, ".") || strings.HasPrefix(name, "_") {
			continue
		}
		md := filepath.Join(tasksDir, name, "task.md")
		st, err := os.Stat(md)
		if err != nil {
			continue
		}
		hdr, ok := readYAMLHeader(md)
		if !ok {
			continue
		}
		status := strings.TrimSpace(hdr["status"])
		if status == "in_progress" || status == "reviewing" || strings.HasPrefix(status, "waiting_") {
			cands = append(cands, cand{name, st.ModTime()})
		}
	}
	if len(cands) == 0 {
		return ""
	}
	sort.Slice(cands, func(i, j int) bool { return cands[i].mt.After(cands[j].mt) })
	return cands[0].name
}

// ListTasks returns every task dir under root/tasks/ with status + mtime,
// sorted by mtime desc. Used by the task-switch modal.
func ListTasks(root string) []model.TaskBrief {
	tasksDir := filepath.Join(root, "tasks")
	entries, err := os.ReadDir(tasksDir)
	if err != nil {
		return nil
	}
	var out []model.TaskBrief
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasPrefix(name, ".") || strings.HasPrefix(name, "_") {
			continue
		}
		md := filepath.Join(tasksDir, name, "task.md")
		st, err := os.Stat(md)
		if err != nil {
			continue
		}
		hdr, _ := readYAMLHeader(md)
		status := "unknown"
		if hdr != nil {
			if s := strings.TrimSpace(hdr["status"]); s != "" {
				status = s
			}
		}
		out = append(out, model.TaskBrief{
			Name:      name,
			Status:    status,
			UpdatedAt: st.ModTime(),
		})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].UpdatedAt.After(out[j].UpdatedAt) })
	return out
}
