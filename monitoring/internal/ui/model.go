package ui

import (
	"context"
	"errors"
	"fmt"
	"time"

	tea "github.com/charmbracelet/bubbletea"

	"github.com/netwaif/mat/internal/coach"
	"github.com/netwaif/mat/internal/model"
	"github.com/netwaif/mat/internal/parser"
)

type mode int

const (
	modeMain mode = iota
	modeModal
	modeLogModal
	modeUsage
)

// tickInterval is the auto-refresh polling period for the main view.
const tickInterval = 2 * time.Second

// usageTickInterval is the auto-refresh period for the usage view. It is
// far slower than the main view's 2s because `coach --json` queries three
// providers sequentially via codexbar and is slow; 30s matches `coach
// --watch`'s own default. Polling only runs while the usage view is open.
const usageTickInterval = 30 * time.Second

// Model is the bubbletea root model.
type Model struct {
	root        string
	taskName    string
	task        model.Task
	loaded      bool
	loadErr     string
	mode        mode
	modalItems  []model.TaskBrief
	modalCursor int
	logScroll   int // top-of-window offset for the log modal
	width       int
	height      int
	startupOpen bool

	// --- usage view (coach --json) state ---
	usage          coach.Snapshot // last successful snapshot
	usageHasData   bool           // a snapshot has been fetched at least once
	usageErr       string         // last fetch error, "" when healthy
	usageLoading   bool           // a fetch is in flight (drives "갱신 중")
	usageActive    bool           // usage view open ⇒ polling armed
	usageFetchedAt time.Time      // wall-clock of last successful fetch
}

func NewModel(root, taskName string) Model {
	return Model{root: root, taskName: taskName}
}

func (m Model) WithStartupModal() Model {
	m.startupOpen = true
	return m
}

// --- messages ---

type loadedMsg struct {
	task model.Task
	err  error
}

type modalListMsg struct {
	items []model.TaskBrief
}

type tickMsg time.Time

type usageLoadedMsg struct {
	snap coach.Snapshot
	err  error
}

type usageTickMsg time.Time

// --- commands ---

func loadTaskCmd(root, name string) tea.Cmd {
	return func() tea.Msg {
		if name == "" {
			return loadedMsg{err: fmt.Errorf("no active task")}
		}
		t, err := parser.LoadTask(root, name)
		return loadedMsg{task: t, err: err}
	}
}

func loadModalCmd(root string) tea.Cmd {
	return func() tea.Msg {
		return modalListMsg{items: parser.ListTasks(root)}
	}
}

func tickCmd() tea.Cmd {
	return tea.Tick(tickInterval, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

// fetchUsageCmd runs `coach --json` off the UI loop (bubbletea runs the
// returned closure in its own goroutine), so the view never blocks while
// codexbar churns. The result arrives as a usageLoadedMsg.
func fetchUsageCmd() tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		snap, err := coach.Fetch(ctx)
		return usageLoadedMsg{snap: snap, err: err}
	}
}

func usageTickCmd() tea.Cmd {
	return tea.Tick(usageTickInterval, func(t time.Time) tea.Msg {
		return usageTickMsg(t)
	})
}

// --- bubbletea contract ---

func (m Model) Init() tea.Cmd {
	if m.startupOpen {
		return tea.Batch(loadModalCmd(m.root), tickCmd())
	}
	return tea.Batch(loadTaskCmd(m.root, m.taskName), tickCmd())
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		// Re-clamp the log modal's scroll offset against the new height.
		// Without this, shrinking the terminal while the modal is open
		// leaves logScroll pointing past maxLogScroll(), causing the body
		// to render blank until the user presses j/k/G.
		if m.mode == modeLogModal && m.logScroll > m.maxLogScroll() {
			m.logScroll = m.maxLogScroll()
		}
		return m, nil

	case loadedMsg:
		m.loaded = true
		if msg.err != nil && msg.task.Path == "" {
			m.loadErr = msg.err.Error()
		} else {
			m.loadErr = ""
			m.task = msg.task
		}
		return m, nil

	case modalListMsg:
		m.modalItems = msg.items
		m.modalCursor = 0
		m.mode = modeModal
		if m.startupOpen {
			m.startupOpen = false
		}
		return m, nil

	case tickMsg:
		// Only reload task data when on the main view with an active task.
		// Modal-open (task switch or log) and usage / no-task states only
		// re-arm the ticker so the user's scroll / selection is never
		// disturbed (and so the usage view's slow coach poll runs on its
		// own ticker, not this 2s one).
		if m.mode == modeMain && m.taskName != "" {
			return m, tea.Batch(loadTaskCmd(m.root, m.taskName), tickCmd())
		}
		return m, tickCmd()

	case usageLoadedMsg:
		m.usageLoading = false
		if msg.err != nil {
			if errors.Is(msg.err, coach.ErrNotInstalled) {
				m.usageErr = "coach 미설치 (PATH에 coach 없음)"
			} else {
				m.usageErr = "갱신 실패: " + msg.err.Error()
			}
			// Keep any prior snapshot on screen (stale) rather than
			// wiping it — usageHasData is left as-is.
			return m, nil
		}
		m.usage = msg.snap
		m.usageHasData = true
		m.usageErr = ""
		m.usageFetchedAt = time.Now()
		return m, nil

	case usageTickMsg:
		// Poll only while the usage view is open. Leaving the view clears
		// usageActive, so the in-flight tick fires once here and stops
		// re-arming — no background polling. Skip a fetch if one is still
		// in flight to avoid overlapping coach invocations.
		if m.mode != modeUsage || !m.usageActive {
			return m, nil
		}
		if m.usageLoading {
			return m, usageTickCmd()
		}
		m.usageLoading = true
		return m, tea.Batch(fetchUsageCmd(), usageTickCmd())

	case tea.KeyMsg:
		return m.handleKey(msg)
	}
	return m, nil
}

func (m Model) handleKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch m.mode {
	case modeModal:
		switch msg.String() {
		case "esc", "q":
			if m.taskName == "" {
				// nothing to fall back to
				return m, tea.Quit
			}
			m.mode = modeMain
			return m, nil
		case "ctrl+c":
			return m, tea.Quit
		case "j", "down":
			if m.modalCursor < len(m.modalItems)-1 {
				m.modalCursor++
			}
			return m, nil
		case "k", "up":
			if m.modalCursor > 0 {
				m.modalCursor--
			}
			return m, nil
		case "enter":
			if len(m.modalItems) == 0 {
				return m, nil
			}
			sel := m.modalItems[m.modalCursor]
			m.taskName = sel.Name
			m.mode = modeMain
			m.loaded = false
			m.logScroll = 0
			return m, loadTaskCmd(m.root, m.taskName)
		}
		return m, nil

	case modeUsage:
		switch msg.String() {
		case "esc", "u":
			// back to the main view; disarm the usage poller so the
			// pending tick stops re-arming.
			m.mode = modeMain
			m.usageActive = false
			return m, nil
		case "q", "ctrl+c":
			return m, tea.Quit
		case "r":
			// manual refresh; ignore if a fetch is already in flight.
			if !m.usageLoading {
				m.usageLoading = true
				return m, fetchUsageCmd()
			}
			return m, nil
		}
		return m, nil

	case modeLogModal:
		switch msg.String() {
		case "esc", "q":
			m.mode = modeMain
			return m, nil
		case "ctrl+c":
			return m, tea.Quit
		case "j", "down":
			max := m.maxLogScroll()
			if m.logScroll < max {
				m.logScroll++
			}
			return m, nil
		case "k", "up":
			if m.logScroll > 0 {
				m.logScroll--
			}
			return m, nil
		case "g", "home":
			m.logScroll = 0
			return m, nil
		case "G", "end":
			m.logScroll = m.maxLogScroll()
			return m, nil
		}
		return m, nil

	default: // modeMain
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "r":
			if m.taskName == "" {
				return m, loadModalCmd(m.root)
			}
			return m, loadTaskCmd(m.root, m.taskName)
		case "t":
			return m, loadModalCmd(m.root)
		case "l", "L":
			if m.taskName == "" {
				return m, nil
			}
			// open log modal pinned to the latest line.
			m.mode = modeLogModal
			m.logScroll = m.maxLogScroll()
			return m, nil
		case "u":
			// switch to the usage view: fetch once on entry and arm the
			// slow poller (guarded so re-entry never stacks tickers).
			m.mode = modeUsage
			var cmds []tea.Cmd
			if !m.usageLoading {
				m.usageLoading = true
				cmds = append(cmds, fetchUsageCmd())
			}
			if !m.usageActive {
				m.usageActive = true
				cmds = append(cmds, usageTickCmd())
			}
			return m, tea.Batch(cmds...)
		}
	}
	return m, nil
}

// maxLogScroll returns the largest valid logScroll offset given the
// current terminal height. Computed against logModalBodyHeight so the
// last line is always reachable but never goes past it.
func (m Model) maxLogScroll() int {
	n := len(m.task.LogTail)
	body := m.logModalBodyHeight()
	if n <= body {
		return 0
	}
	return n - body
}
