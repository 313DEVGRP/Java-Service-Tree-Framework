package ui

import (
	"strings"
	"testing"

	"github.com/charmbracelet/lipgloss"

	"github.com/netwaif/mat/internal/coach"
	"github.com/netwaif/mat/internal/model"
)

func TestStatusStyleReviewingPending(t *testing.T) {
	if got := statusStyle("reviewing").GetForeground(); got != colorReview {
		t.Errorf("statusStyle(reviewing) fg = %v, want colorReview %v", got, colorReview)
	}
	if got := statusStyle("pending").GetForeground(); got != colorMuted {
		t.Errorf("statusStyle(pending) fg = %v, want colorMuted %v", got, colorMuted)
	}
	// existing cases unchanged
	if got := statusStyle("done").GetForeground(); got != colorOK {
		t.Errorf("statusStyle(done) fg = %v, want colorOK %v", got, colorOK)
	}
}

// widestLogLine returns the max cell width among the indented log rows
// (everything after the section-title line) of a renderLog result.
func widestLogLine(out string) int {
	max := 0
	for _, ln := range strings.Split(out, "\n") {
		if !strings.HasPrefix(ln, "  ") {
			continue // section title row has no indent
		}
		if w := lipgloss.Width(ln); w > max {
			max = w
		}
	}
	return max
}

func TestRenderLogWidthAware(t *testing.T) {
	long := strings.Repeat("x", 200)
	tail := []string{long}

	narrow := renderLog(tail, 5, 20)
	wide := renderLog(tail, 5, 250)

	if !strings.Contains(narrow, "…") {
		t.Errorf("narrow renderLog should clip with …:\n%s", narrow)
	}
	// row = 2-space indent + up-to-`width` cells of text.
	if got := widestLogLine(narrow); got > 2+20 {
		t.Errorf("narrow log row width = %d, want <= %d", got, 2+20)
	}
	if strings.Contains(wide, "…") {
		t.Errorf("wide renderLog should not clip a 200-char line:\n%s", wide)
	}
	if !strings.Contains(wide, long) {
		t.Errorf("wide renderLog dropped content; want full line present")
	}
	if narrow == wide {
		t.Errorf("renderLog ignored width: narrow and wide identical")
	}
}

func TestRenderLogCJKCellBound(t *testing.T) {
	// Each 한 is 2 cells wide; truncate must bound by cell width, not rune
	// count, so a Korean-heavy line cannot wrap a fixed-height box.
	korean := strings.Repeat("한", 100)
	out := renderLog([]string{korean}, 5, 20)
	if !strings.Contains(out, "…") {
		t.Errorf("CJK line should clip with …:\n%s", out)
	}
	if got := widestLogLine(out); got > 2+20 {
		t.Errorf("CJK log row width = %d cells, want <= %d", got, 2+20)
	}
}

// TestRenderLogBoxNoWrap guards the call-site arithmetic in renderMain:
// boxStyle.Width(inner).Render(renderLog(..., inner-4)). The unit tests
// above only exercise renderLog's own contract; an off-by-one at the call
// site (e.g. inner-3) would slip past them but show up here as an extra
// wrapped row inside the box. Uses CJK to also stress wide-rune width.
func TestRenderLogBoxNoWrap(t *testing.T) {
	const inner = 50
	long := strings.Repeat("한", 100) // 200 cells, far past the box
	box := boxStyle.Width(inner).Render(renderLog([]string{long}, 5, inner-4))

	// title row + 1 log row + rounded top/bottom border = 4 rows.
	// inner-3 → indent2 + (inner-3) = inner-1 > wrapAt(inner-2) → wraps → 5.
	if h := lipgloss.Height(box); h != 4 {
		t.Errorf("log box height = %d, want 4 (off-by-one width → wrap):\n%s", h, box)
	}
	if w := lipgloss.Width(box); w != inner+2 { // +2 for left/right border
		t.Errorf("log box width = %d, want %d", w, inner+2)
	}
}

func TestRenderArtifacts(t *testing.T) {
	out := renderArtifacts([]model.Artifact{
		{Name: "review-report.md", Size: 10759},
		{Name: "src", IsDir: true, Count: 3},
	})
	for _, want := range []string{"Artifacts", "review-report.md", "src", "3"} {
		if !strings.Contains(out, want) {
			t.Errorf("renderArtifacts output missing %q:\n%s", want, out)
		}
	}
}

// coach reports the Fable 5 weekly window (fable_7d) only on Max plans;
// the usage view must show it as a "Fable" row when present and render
// nothing extra when absent (basic plans).
func TestRenderProviderFableWindow(t *testing.T) {
	withFable := coach.Provider{
		Ok: true, Plan: "Claude Max 5x", Level: "green",
		Windows: map[string]coach.Window{
			"5h":       {LeftPct: 96, ResetMin: 235},
			"7d":       {LeftPct: 45, ResetMin: 1125},
			"fable_7d": {LeftPct: 25, ResetMin: 1125},
		},
	}
	out := renderProvider("claude", withFable, true, 70)
	if !strings.Contains(out, "Fable") {
		t.Errorf("fable_7d present but no Fable row:\n%s", out)
	}
	if strings.Contains(out, "fable_7d") {
		t.Errorf("raw fable_7d key leaked into output:\n%s", out)
	}

	withoutFable := coach.Provider{
		Ok: true, Plan: "Claude Pro", Level: "green",
		Windows: map[string]coach.Window{
			"5h": {LeftPct: 96, ResetMin: 235},
			"7d": {LeftPct: 45, ResetMin: 1125},
		},
	}
	out = renderProvider("claude", withoutFable, true, 70)
	if strings.Contains(out, "Fable") || strings.Contains(out, "fable") {
		t.Errorf("no fable_7d window but Fable row rendered:\n%s", out)
	}
}
