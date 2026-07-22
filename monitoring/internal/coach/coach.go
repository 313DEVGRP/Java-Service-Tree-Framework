// Package coach is a thin, read-only adapter over the external `coach`
// CLI. It is the *single* data source for mat's usage view: mat shells
// out to `coach --json` and decodes the result — it deliberately does NOT
// reimplement codexbar parsing or any quota/policy judgement. coach owns
// the policy; mat only renders what coach reports.
//
// This package is intentionally separate from internal/parser (which is
// specific to the multi-agent starter filesystem) so the one-directional
// "data source → model → ui" layering is preserved and the starter root
// stays untouched by the usage feature.
package coach

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os/exec"
)

// ErrNotInstalled is returned by Fetch when the `coach` binary cannot be
// found on PATH. Callers surface this as a graceful "coach 미설치" state
// rather than crashing.
var ErrNotInstalled = errors.New("coach not installed")

// Window is one rolling usage window (e.g. "5h", "7d"). Fields mirror the
// `coach --json` schema exactly.
type Window struct {
	LeftPct  int `json:"left_pct"`
	ResetMin int `json:"reset_min"`
}

// Provider is one usage provider (claude / codex / antigravity). Windows
// is a map because not every provider reports every window — antigravity,
// for instance, only reports "7d".
type Provider struct {
	Ok      bool              `json:"ok"`
	Plan    string            `json:"plan"`
	Level   string            `json:"level"`
	Action  string            `json:"action"`
	Reason  string            `json:"reason"`
	Windows map[string]Window `json:"windows"`
}

// Snapshot is the full `coach --json` payload.
type Snapshot struct {
	TS        string              `json:"ts"`
	Providers map[string]Provider `json:"providers"`
}

// Fetch runs `coach --json` and decodes its output. It is meant to be
// called from a goroutine (a bubbletea command), never on the UI loop:
// codexbar queries three providers sequentially and can take several
// seconds. The ctx deadline bounds that wait.
//
// Contract: never panics. A missing binary yields ErrNotInstalled; any
// other failure (non-zero exit, malformed JSON, timeout) yields a wrapped
// error. On success the returned Snapshot is fully populated.
func Fetch(ctx context.Context) (Snapshot, error) {
	if _, err := exec.LookPath("coach"); err != nil {
		return Snapshot{}, ErrNotInstalled
	}
	out, err := exec.CommandContext(ctx, "coach", "--json").Output()
	if err != nil {
		if errors.Is(err, exec.ErrNotFound) {
			return Snapshot{}, ErrNotInstalled
		}
		return Snapshot{}, fmt.Errorf("coach --json 실패: %w", err)
	}
	var s Snapshot
	if err := json.Unmarshal(out, &s); err != nil {
		return Snapshot{}, fmt.Errorf("coach 출력 파싱 실패: %w", err)
	}
	return s, nil
}
