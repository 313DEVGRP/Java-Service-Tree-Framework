package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	tea "github.com/charmbracelet/bubbletea"

	"github.com/netwaif/mat/internal/model"
	"github.com/netwaif/mat/internal/parser"
	"github.com/netwaif/mat/internal/ui"
)

func main() {
	root, err := resolveRoot()
	if err != nil {
		fmt.Fprintln(os.Stderr, "mat:", err)
		os.Exit(1)
	}

	var initialTask string
	if len(os.Args) >= 2 {
		initialTask = os.Args[1]
	} else {
		initialTask = parser.PickActiveTask(root)
	}

	m := ui.NewModel(root, initialTask)
	if initialTask == "" {
		// no active candidate -> open modal immediately
		m = m.WithStartupModal()
	}

	p := tea.NewProgram(m, tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "mat:", err)
		os.Exit(1)
	}

	_ = model.NilSnapshot // keep model import in case ui shrinks; harmless
	_ = filepath.Separator
}

func resolveRoot() (string, error) {
	if v := os.Getenv("MAT_ROOT"); v != "" {
		abs, err := filepath.Abs(expandHome(v))
		if err != nil {
			return "", err
		}
		return abs, nil
	}
	if home, err := os.UserHomeDir(); err == nil {
		if data, err := os.ReadFile(filepath.Join(home, ".config", "mat", "root")); err == nil {
			if line := strings.TrimSpace(string(data)); line != "" {
				abs, err := filepath.Abs(expandHome(line))
				if err != nil {
					return "", err
				}
				return abs, nil
			}
		}
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	return cwd, nil
}

func expandHome(p string) string {
	if len(p) >= 2 && p[:2] == "~/" {
		if home, err := os.UserHomeDir(); err == nil {
			return filepath.Join(home, p[2:])
		}
	}
	return p
}
