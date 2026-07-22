package ui

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"

	"github.com/netwaif/mat/internal/coach"
	"github.com/netwaif/mat/internal/model"
)

var (
	colorBorder = lipgloss.Color("240")
	colorAccent = lipgloss.Color("39")
	colorMuted  = lipgloss.Color("245")
	colorWarn   = lipgloss.Color("214")
	colorErr    = lipgloss.Color("203")
	colorOK     = lipgloss.Color("42")
	colorReview = lipgloss.Color("213")

	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colorAccent)

	sectionTitleStyle = lipgloss.NewStyle().
				Bold(true).
				Foreground(colorMuted)

	mutedStyle = lipgloss.NewStyle().Foreground(colorMuted)

	boxStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorBorder).
			Padding(0, 1)

	modalStyle = lipgloss.NewStyle().
			Border(lipgloss.DoubleBorder()).
			BorderForeground(colorAccent).
			Padding(0, 1)

	statusStyle = func(s string) lipgloss.Style {
		base := lipgloss.NewStyle().Bold(true)
		switch {
		case s == "done":
			return base.Foreground(colorOK)
		case strings.HasPrefix(s, "waiting_"):
			return base.Foreground(colorWarn)
		case s == "in_progress":
			return base.Foreground(colorAccent)
		case s == "reviewing":
			return base.Foreground(colorReview)
		case s == "pending":
			return base.Foreground(colorMuted)
		case s == "unknown":
			return base.Foreground(colorErr)
		default:
			return base.Foreground(colorMuted)
		}
	}
)

// minLogLines is the floor for the main-view log box; we never collapse
// below this even on a tiny (e.g. 80x24) terminal — better to clip the
// box than to show 0 log lines.
const minLogLines = 5

// logBoxChrome accounts for the lipgloss roundedBorder (top+bottom = 2)
// plus the section title row inside the box. Padding is 0 vertically.
const logBoxChrome = 3

func (m Model) View() string {
	// The usage view is a full-screen replacement (not an overlay) and is
	// independent of task loading, so it short-circuits before the task
	// loading guard below.
	if m.mode == modeUsage {
		return m.renderUsage()
	}
	if !m.loaded && m.mode != modeModal {
		return mutedStyle.Render("loading…  (root: " + m.root + ")")
	}
	mainView := m.renderMain()
	switch m.mode {
	case modeModal:
		return overlayCenter(mainView, m.renderModal(), m.width, m.height)
	case modeLogModal:
		return overlayCenter(mainView, m.renderLogModal(), m.width, m.height)
	}
	return mainView
}

func (m Model) renderMain() string {
	width := m.width
	if width <= 0 {
		width = 78
	}
	inner := width - 4
	if inner < 30 {
		inner = 30
	}

	// --- pieces above the log box ---
	title := headerStyle.Render("mat") + "  —  Task: " + boldStr(m.taskName)
	statusLine := ""
	if m.taskName != "" {
		statusLine = "Status: " + statusStyle(m.task.Status).Render(m.task.Status) +
			"   ·   Updated: " + m.task.UpdatedAt.Format("15:04")
	} else if m.loadErr != "" {
		statusLine = mutedStyle.Render(m.loadErr)
	}
	headerBox := boxStyle.Width(inner).Render(title + "\n" + statusLine)

	if m.taskName == "" {
		var b strings.Builder
		b.WriteString(headerBox)
		b.WriteString("\n")
		b.WriteString(mutedStyle.Render("No active task. Press [t] to choose, [q] to quit."))
		b.WriteString("\n")
		b.WriteString(footerHelp())
		return b.String()
	}

	var parseErrBox string
	if m.task.ParseError != "" {
		warn := lipgloss.NewStyle().Foreground(colorErr).Render("⚠ " + m.task.ParseError)
		parseErrBox = boxStyle.Width(inner).Render(warn)
	}

	goalText := m.task.Goal
	if goalText == "" {
		goalText = mutedStyle.Render("(no Goal section)")
	}
	goalBox := boxStyle.Width(inner).Render(sectionTitleStyle.Render("Goal") + "\n" + goalText)

	workersBox := boxStyle.Width(inner).Render(renderWorkers(m.task.Workers))

	var artifactsBox string
	if len(m.task.Artifacts) > 0 {
		artifactsBox = boxStyle.Width(inner).Render(renderArtifacts(m.task.Artifacts))
	}

	footer := footerHelp()

	// --- compute how many log lines fit in remaining vertical space ---
	// Each non-log block contributes Height(box) + 1 to account for the
	// trailing "\n" written between blocks. Footer is the last line and
	// has no trailing "\n", so it contributes only Height(footer). The
	// log box itself also has a "\n" separator after it (between logBox
	// and footer) — that single newline is the trailing "- 1" below.
	usedRows := lipgloss.Height(headerBox) + 1 // box + trailing \n
	if parseErrBox != "" {
		usedRows += lipgloss.Height(parseErrBox) + 1
	}
	usedRows += lipgloss.Height(goalBox) + 1
	usedRows += lipgloss.Height(workersBox) + 1
	if artifactsBox != "" {
		usedRows += lipgloss.Height(artifactsBox) + 1
	}
	usedRows += lipgloss.Height(footer) // no trailing \n after footer

	logLines := minLogLines
	if m.height > 0 {
		remaining := m.height - usedRows - logBoxChrome - 1
		if remaining > logLines {
			logLines = remaining
		}
	}

	// logTextWidth is the cell budget for a single log line's text.
	// boxStyle.Width(inner) sets the pre-border block width; lipgloss wraps
	// content at inner - horizontalPadding (= inner-2, padding is 0,1). Each
	// log line is rendered with a 2-space indent, so the text itself gets
	// inner-4 (2 indent + inner-4 = inner-2 = the wrap point, no wrap). This
	// mirrors renderLogModal's `inner-2` (no indent there).
	logTextWidth := inner - 4
	logBox := boxStyle.Width(inner).Render(renderLog(m.task.LogTail, logLines, logTextWidth))

	// --- assemble ---
	var b strings.Builder
	b.WriteString(headerBox)
	b.WriteString("\n")
	if parseErrBox != "" {
		b.WriteString(parseErrBox)
		b.WriteString("\n")
	}
	b.WriteString(goalBox)
	b.WriteString("\n")
	b.WriteString(workersBox)
	b.WriteString("\n")
	if artifactsBox != "" {
		b.WriteString(artifactsBox)
		b.WriteString("\n")
	}
	b.WriteString(logBox)
	b.WriteString("\n")
	b.WriteString(footer)
	return b.String()
}

func renderWorkers(ws []model.Worker) string {
	var b strings.Builder
	b.WriteString(sectionTitleStyle.Render("Workers"))
	b.WriteString("\n")
	if len(ws) == 0 {
		b.WriteString(mutedStyle.Render("  (none)"))
		return b.String()
	}
	for i, w := range ws {
		if i > 0 {
			b.WriteString("\n")
		}
		head := fmt.Sprintf("  %s %-18s  %s",
			w.State.Icon(),
			w.Role,
			w.State.Label(),
		)
		if !w.UpdatedAt.IsZero() {
			head += "   " + mutedStyle.Render(w.UpdatedAt.Format("15:04"))
		}
		b.WriteString(head)
		if w.Purpose != "" {
			b.WriteString("\n")
			b.WriteString("        " + truncate(w.Purpose, 60))
		}
		switch {
		case w.HasResult:
			b.WriteString("\n")
			b.WriteString("        " + mutedStyle.Render(
				fmt.Sprintf("result.md: %s (%s)", shortPath(w.ResultPath), humanSize(w.ResultSize))))
		case w.HasBrief:
			b.WriteString("\n")
			b.WriteString("        " + mutedStyle.Render(
				fmt.Sprintf("brief.md: %s (%d자)", shortPath(w.BriefPath), w.BriefChars)))
		case w.FromPlanned:
			b.WriteString("\n")
			b.WriteString("        " + mutedStyle.Render("실행 예정"))
		}
	}
	return b.String()
}

// renderArtifacts renders the task-level artifacts/ box. Only called when
// there is at least one entry (renderMain keeps the box out of the layout
// arithmetic otherwise, so the empty common case wastes no rows).
func renderArtifacts(arts []model.Artifact) string {
	var b strings.Builder
	b.WriteString(sectionTitleStyle.Render("Artifacts"))
	for _, a := range arts {
		b.WriteString("\n  ")
		if a.IsDir {
			b.WriteString(truncate(fmt.Sprintf("%s/  (%d files)", a.Name, a.Count), 70))
		} else {
			b.WriteString(truncate(fmt.Sprintf("%s  (%s)", a.Name, humanSize(a.Size)), 70))
		}
	}
	return b.String()
}

// renderLog renders the tail of the log into the main view. `limit` is the
// maximum number of lines to show (computed from terminal height in
// renderMain). `width` is the per-line cell budget, derived from the terminal
// width by the caller so long lines clip with `…` relative to the actual box
// size instead of a fixed 80 (matching the [L] modal's width-aware behavior).
// width is taken as-is — truncate() handles degenerate values (n<=0 → "",
// n==1 → "…") gracefully, and the only caller (renderMain) always passes
// inner-4 ≥ 26, so no clamp is applied (a floor would risk exceeding the
// caller's actual box width and forcing a wrap). The section title reflects
// how many we are showing vs total so the user knows there is more in [L].
func renderLog(tail []string, limit, width int) string {
	if limit < 1 {
		limit = 1
	}
	var shown []string
	if len(tail) > limit {
		shown = tail[len(tail)-limit:]
	} else {
		shown = tail
	}

	var b strings.Builder
	titleText := fmt.Sprintf("Recent log (last %d of %d)", len(shown), len(tail))
	if len(tail) == 0 {
		titleText = "Recent log"
	}
	b.WriteString(sectionTitleStyle.Render(titleText))
	b.WriteString("\n")
	if len(tail) == 0 {
		b.WriteString(mutedStyle.Render("  (empty)"))
		return b.String()
	}
	for _, ln := range shown {
		b.WriteString("  ")
		b.WriteString(truncate(ln, width))
		b.WriteString("\n")
	}
	return strings.TrimRight(b.String(), "\n")
}

func footerHelp() string {
	return mutedStyle.Render(" 자동 갱신 2s · [r] 즉시   [t] 작업 전환   [L] 로그   [u] 사용량   [q] 종료")
}

// usageProviderOrder fixes the display order of the three providers,
// independent of Go's random map iteration.
var usageProviderOrder = []string{"claude", "codex", "antigravity"}

// usageWindowOrder fixes the order of windows within a provider. Providers
// that omit a window (antigravity has no 5h; fable_7d only exists on Max
// plans) simply skip it.
var usageWindowOrder = []string{"5h", "7d", "fable_7d"}

// usageWindowLabel maps a coach window key to its display label, mirroring
// coach's own rendering of the Fable 5 weekly window.
var usageWindowLabel = map[string]string{"fable_7d": "Fable"}

// windowLabel returns the display label for a window key, falling back to
// the raw key for windows coach may add later.
func windowLabel(key string) string {
	if l, ok := usageWindowLabel[key]; ok {
		return l
	}
	return key
}

// usageProviderColor mirrors coach's PROV_COLOR (claude=yellow, codex=cyan,
// antigravity=magenta) so mat's usage view reads the same as coach itself.
var usageProviderColor = map[string]lipgloss.Color{
	"claude":      lipgloss.Color("3"),
	"codex":       lipgloss.Color("6"),
	"antigravity": lipgloss.Color("5"),
}

// providerColor returns the coach-matched color for a provider key, falling
// back to the generic accent for providers coach may add later.
func providerColor(key string) lipgloss.Color {
	if c, ok := usageProviderColor[key]; ok {
		return c
	}
	return colorAccent
}

func usageFooter() string {
	return mutedStyle.Render(" 자동 갱신 30s · [r] 즉시   [u/esc] 돌아가기   [q] 종료")
}

// renderUsage draws the full-screen usage view from the last coach
// snapshot. mat never reimplements coach's judgement — it only formats the
// reported plan/level/action/reason and the per-window left%/reset.
func (m Model) renderUsage() string {
	width := m.width
	if width <= 0 {
		width = 78
	}
	inner := width - 4
	if inner < 30 {
		inner = 30
	}

	var b strings.Builder

	title := headerStyle.Render("mat") + "  —  사용량"
	switch {
	case m.usageLoading:
		title += "   " + lipgloss.NewStyle().Foreground(colorAccent).Render("· 갱신 중…")
	case !m.usageFetchedAt.IsZero():
		title += "   " + mutedStyle.Render("· Updated "+m.usageFetchedAt.Format("15:04:05"))
	}
	b.WriteString(boxStyle.Width(inner).Render(title))
	b.WriteString("\n")

	switch {
	case !m.usageHasData && m.usageErr != "":
		// hard failure before any data (e.g. coach 미설치)
		b.WriteString(boxStyle.Width(inner).Render(
			lipgloss.NewStyle().Foreground(colorErr).Render("⚠ " + m.usageErr)))
		b.WriteString("\n")
	case !m.usageHasData:
		// first fetch in flight, nothing to show yet
		b.WriteString(boxStyle.Width(inner).Render(
			mutedStyle.Render("coach 실행 중… (codexbar는 느릴 수 있어요)")))
		b.WriteString("\n")
	default:
		for _, key := range usageProviderOrder {
			prov, ok := m.usage.Providers[key]
			b.WriteString(boxStyle.Width(inner).Render(renderProvider(key, prov, ok, inner-2)))
			b.WriteString("\n")
		}
		// a refresh that failed while we still hold a prior snapshot:
		// keep the stale data above, note the failure inline.
		if m.usageErr != "" {
			b.WriteString(mutedStyle.Render(" ⚠ " + truncate(m.usageErr, inner)))
			b.WriteString("\n")
		}
	}

	b.WriteString(usageFooter())
	return b.String()
}

// renderProvider renders one provider box body. `present` is false when the
// snapshot has no entry for this provider key at all. textWidth is the cell
// budget for wrapping/truncating the longer free-text lines.
func renderProvider(label string, p coach.Provider, present bool, textWidth int) string {
	var b strings.Builder

	if !present {
		b.WriteString(sectionTitleStyle.Render(label))
		b.WriteString("\n  ")
		b.WriteString(mutedStyle.Render("데이터 없음"))
		return b.String()
	}

	dot := lipgloss.NewStyle().Foreground(levelColor(p.Level)).Render("●")
	name := lipgloss.NewStyle().Bold(true).Foreground(providerColor(label)).Render(label)
	b.WriteString(fmt.Sprintf("%s %s  %s", dot, name, mutedStyle.Render(p.Plan)))

	if !p.Ok {
		b.WriteString("\n  ")
		b.WriteString(mutedStyle.Render("데이터 없음"))
		if p.Reason != "" {
			b.WriteString("\n  ")
			b.WriteString(mutedStyle.Render(truncate(p.Reason, textWidth-2)))
		}
		return b.String()
	}

	if p.Action != "" {
		b.WriteString("\n  ")
		b.WriteString(lipgloss.NewStyle().Foreground(levelColor(p.Level)).
			Render(truncate(p.Action, textWidth-2)))
	}

	for _, wk := range usageWindowOrder {
		w, has := p.Windows[wk]
		if !has {
			continue
		}
		b.WriteString("\n  ")
		b.WriteString(fmt.Sprintf("%-5s %s %3d%%  · 리셋 %s",
			windowLabel(wk), usageBar(w.LeftPct, 10, providerColor(label)), w.LeftPct, humanizeReset(w.ResetMin)))
	}

	if p.Reason != "" {
		b.WriteString("\n  ")
		b.WriteString(mutedStyle.Render(truncate(p.Reason, textWidth-2)))
	}
	return b.String()
}

// levelColor maps coach's level string to a mat palette color. Unknown
// levels fall back to muted so an added level never crashes or mis-signals.
func levelColor(level string) lipgloss.Color {
	switch level {
	case "green":
		return colorOK
	case "yellow", "amber", "warn", "warning":
		return colorWarn
	case "red", "danger", "critical":
		return colorErr
	default:
		return colorMuted
	}
}

// usageBar renders a left%-filled bar of the given cell width, filled in the
// caller's per-provider color.
func usageBar(pct, width int, fill lipgloss.Color) string {
	if width <= 0 {
		width = 10
	}
	if pct < 0 {
		pct = 0
	}
	if pct > 100 {
		pct = 100
	}
	filled := (pct*width + 50) / 100 // round to nearest cell
	if filled > width {
		filled = width
	}
	return lipgloss.NewStyle().Foreground(fill).Render(strings.Repeat("▓", filled)) +
		mutedStyle.Render(strings.Repeat("░", width-filled))
}

// humanizeReset turns a minutes-until-reset count into a compact human
// string: "45m", "2h19m", "2d3h".
func humanizeReset(min int) string {
	if min <= 0 {
		return "곧"
	}
	if min < 60 {
		return fmt.Sprintf("%dm", min)
	}
	h := min / 60
	mm := min % 60
	if h < 24 {
		if mm == 0 {
			return fmt.Sprintf("%dh", h)
		}
		return fmt.Sprintf("%dh%dm", h, mm)
	}
	d := h / 24
	hh := h % 24
	if hh == 0 {
		return fmt.Sprintf("%dd", d)
	}
	return fmt.Sprintf("%dd%dh", d, hh)
}

func (m Model) renderModal() string {
	var b strings.Builder
	b.WriteString(headerStyle.Render("Tasks") + "  " + mutedStyle.Render("(j/k 이동, enter 선택, esc 취소)"))
	b.WriteString("\n\n")
	if len(m.modalItems) == 0 {
		b.WriteString(mutedStyle.Render("  (no tasks found under " + m.root + "/tasks)"))
	}
	for i, it := range m.modalItems {
		cursor := "  "
		row := fmt.Sprintf("%-28s  %s", truncate(it.Name, 28), it.Status)
		if i == m.modalCursor {
			cursor = "→ "
			row = lipgloss.NewStyle().Foreground(colorAccent).Bold(true).Render(row)
		}
		b.WriteString(cursor)
		b.WriteString(row)
		b.WriteString("\n")
	}
	b.WriteString("\n")
	b.WriteString(mutedStyle.Render(" [esc] 취소"))
	return modalStyle.Render(b.String())
}

// logModalBodyHeight is the number of log lines the log modal can show
// at the current terminal height (excludes the modal's own chrome and
// the title/footer lines inside the modal box).
//
// chrome breakdown:
//
//	doubleBorder top+bottom .... 2
//	title line ................. 1
//	blank line after title ..... 1
//	blank line before footer ... 1
//	footer/indicator line ...... 1
//	safety margin .............. 1
//	---------------------------------
//	total ...................... 7
//
// This keeps the modal one row shy of m.height so a stray re-render or
// terminal status row never clips the indicator line.
func (m Model) logModalBodyHeight() int {
	const chrome = 7
	body := m.height - chrome
	if body < 5 {
		body = 5
	}
	return body
}

// renderLogModal renders the full log inside a near-fullscreen modal.
// j/k scroll, g/G jump to top/bottom, esc closes.
func (m Model) renderLogModal() string {
	w := m.width
	if w <= 0 {
		w = 78
	}
	inner := w - 4
	if inner < 30 {
		inner = 30
	}

	body := m.logModalBodyHeight()
	total := len(m.task.LogTail)

	var b strings.Builder
	title := headerStyle.Render("Log") + "  " + mutedStyle.Render(
		fmt.Sprintf("(j/k 스크롤, g/G 처음/끝, esc 닫기) · %d줄", total))
	b.WriteString(title)
	b.WriteString("\n\n")

	if total == 0 {
		b.WriteString(mutedStyle.Render("  (empty)"))
		// pad body so the modal stays at a stable size
		for i := 1; i < body; i++ {
			b.WriteString("\n")
		}
	} else {
		start := m.logScroll
		if start < 0 {
			start = 0
		}
		if start > total-1 {
			start = total - 1
		}
		end := start + body
		if end > total {
			end = total
		}
		shown := m.task.LogTail[start:end]
		for i, ln := range shown {
			if i > 0 {
				b.WriteString("\n")
			}
			b.WriteString(truncate(ln, inner-2))
		}
		// pad to body height so the footer stays anchored
		for i := len(shown); i < body; i++ {
			b.WriteString("\n")
		}
		// position indicator
		b.WriteString("\n\n")
		b.WriteString(mutedStyle.Render(
			fmt.Sprintf(" %d–%d / %d", start+1, end, total)))
		return modalStyle.Width(inner).Render(b.String())
	}

	b.WriteString("\n\n")
	b.WriteString(mutedStyle.Render(" [esc] 닫기"))
	return modalStyle.Width(inner).Render(b.String())
}

// --- helpers ---

func boldStr(s string) string {
	return lipgloss.NewStyle().Bold(true).Render(s)
}

// truncate clips s so its visual (cell) width does not exceed n. CJK and
// other wide runes count as 2 cells via lipgloss.Width, matching the way
// the terminal renders them — a rune-count based truncate would let a
// Korean-heavy line wrap to a second row inside a fixed-height box and
// break vertical layout (the log modal regression in particular). When
// the string fits, it is returned unchanged; otherwise we accumulate
// runes until adding the next one would exceed n-1 cells, then append
// "…" (which itself is 1 cell wide).
func truncate(s string, n int) string {
	if n <= 0 {
		return ""
	}
	if lipgloss.Width(s) <= n {
		return s
	}
	if n == 1 {
		// not enough room for content + ellipsis; emit ellipsis alone
		return "…"
	}
	limit := n - 1 // reserve 1 cell for the ellipsis
	var b strings.Builder
	used := 0
	for _, r := range s {
		rw := lipgloss.Width(string(r))
		if used+rw > limit {
			break
		}
		b.WriteRune(r)
		used += rw
	}
	b.WriteRune('…')
	return b.String()
}

func shortPath(p string) string {
	// surface only "workers/<role>/file"
	parts := strings.Split(p, "/")
	for i := 0; i < len(parts)-2; i++ {
		if parts[i] == "workers" {
			return strings.Join(parts[i:], "/")
		}
	}
	return p
}

func humanSize(n int64) string {
	switch {
	case n >= 1024*1024:
		return fmt.Sprintf("%.1fMB", float64(n)/(1024*1024))
	case n >= 1024:
		return fmt.Sprintf("%.1fKB", float64(n)/1024)
	default:
		return fmt.Sprintf("%dB", n)
	}
}

// overlayCenter draws `over` centered on top of `base` by replacing the
// middle rows. bubbletea has no native overlay primitive; we use a coarse
// row-replace which is fine for the modal-on-static-view MVP case.
func overlayCenter(base, over string, w, h int) string {
	if w <= 0 || h <= 0 {
		// no size yet — fall back to concatenation
		return over + "\n\n" + base
	}
	baseLines := strings.Split(base, "\n")
	overLines := strings.Split(over, "\n")
	for len(baseLines) < h {
		baseLines = append(baseLines, "")
	}

	overH := len(overLines)
	if overH > h {
		overH = h
		overLines = overLines[:h]
	}
	overW := 0
	for _, ln := range overLines {
		if l := lipgloss.Width(ln); l > overW {
			overW = l
		}
	}
	startRow := (h - overH) / 2
	if startRow < 0 {
		startRow = 0
	}
	startCol := (w - overW) / 2
	if startCol < 0 {
		startCol = 0
	}

	for i, ln := range overLines {
		row := startRow + i
		if row >= len(baseLines) {
			break
		}
		baseLines[row] = padOrCutLeft(ln, startCol)
	}
	return strings.Join(baseLines, "\n")
}

// padOrCutLeft prepends `pad` spaces to s.
func padOrCutLeft(s string, pad int) string {
	if pad <= 0 {
		return s
	}
	return strings.Repeat(" ", pad) + s
}
