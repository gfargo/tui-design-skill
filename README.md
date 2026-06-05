# tui-design

A Claude Skill for designing and building **clean, professional, minimal terminal UI (TUI) applications and command-line tools** — across Go, Rust, Python, and TypeScript.

Use it for greenfield builds, design reviews, refactors, library decisions, and "should I use Bubble Tea or Ratatui?"-class questions. Covers the universal patterns (layouts, color, keybindings, discoverability) plus per-ecosystem deep-dives for Bubble Tea, Ratatui, Textual, and Ink.

---

> ### 📦 Also in the [`gfargo/skills`](https://github.com/gfargo/skills) marketplace
>
> This skill now also lives in my central skills marketplace, alongside my other skills (like [`vhs-cli-demos`](https://github.com/gfargo/skills), for capturing screenshots + demo GIFs of terminal apps). Add it once and get them all:
>
> ```bash
> /plugin marketplace add gfargo/skills
> /plugin install terminal@gfargo-skills   # → terminal:tui-design  +  terminal:vhs-cli-demos
> ```
>
> This standalone repo still works exactly as before (including `npx skills` and the `.skill` release download) — use it if you only want `tui-design` on its own. The central marketplace is the better pick if you want my whole collection from a single source.

---

## Install

### Option A — Claude Code (plugin marketplace, recommended)

```bash
/plugin marketplace add gfargo/tui-design-skill
/plugin install tui-design@tui-design-marketplace
```

To update later when the skill improves:

```bash
/plugin marketplace update tui-design-marketplace
```

### Option B — Vercel's `npx skills` (cross-agent, no Claude Code required)

If you use Cursor, Codex CLI, Gemini CLI, Aider, Windsurf, or want to install at the project level rather than globally:

```bash
# Install for Claude Code (default)
npx skills add gfargo/tui-design-skill

# Install globally (~/.claude/skills/) instead of project-local
npx skills add gfargo/tui-design-skill -g

# Install for a different agent
npx skills add gfargo/tui-design-skill -a cursor
npx skills add gfargo/tui-design-skill -a codex

# List skills installed via npx skills
npx skills list

# Update later
npx skills update tui-design
```

`npx skills` discovers this skill via the same `marketplace.json` used by Option A, so no extra setup is needed on the repo side.

### Option C — Claude.ai (upload the .skill file)

1. Download the latest [`tui-design.skill`](https://github.com/gfargo/tui-design-skill/releases/latest) from Releases (or build it yourself — see *Build* below).
2. In Claude.ai, go to **Settings → Customize → Skills → Upload skill** and select the file.
3. Toggle the skill on.

> Skills require code execution to be enabled in your Claude.ai settings.

### Option D — Claude Code (direct, without plugin marketplace)

```bash
mkdir -p ~/.claude/skills
cd ~/.claude/skills
git clone https://github.com/gfargo/tui-design-skill.git
ln -s tui-design-skill/plugins/tui-design/skills/tui-design tui-design
```

---

## What the skill covers

The skill is structured so its top-level `SKILL.md` carries the **universal principles** and routes to per-topic reference files on demand. Total: ~4,000 lines across 9 files, but Claude only loads what's relevant to the current question.

**Top-level (`SKILL.md`):**
- Seven canonical TUI layouts (multi-panel, miller columns, drill-down stack, widget dashboard, IDE three-panel, overlay, tabbed-within-panel) — when to use each, what to avoid
- Visual hierarchy in monospace (color, weight, reverse video, borders, density)
- Color as a semantic system, `NO_COLOR`, accessibility tradeoffs
- Two reflexes applied to every layout review — the **clutter audit** (make "feels busy" countable) and **pressure-test the floor** (responsive behavior at 80×24 and narrower), even when the user didn't ask about them
- Cross-app keybinding conventions (`q`, `?`, `/`, `Esc`, `hjkl`, `Tab`, `Ctrl+P`, ...)
- The four non-negotiables: alt screen, panic-safe terminal restore, `SIGWINCH`, `SIGTSTP`
- Decision flow for new TUI/CLI projects
- Review checklist for existing TUIs

**References (loaded as needed):**
- `ecosystem-go.md` — Bubble Tea, Lipgloss, Bubbles, Huh, tview, gocui, Cobra, Wish, gum
- `ecosystem-rust.md` — Ratatui, Crossterm, color-eyre panic safety, Cursive, clap, cliclack, async with Tokio
- `ecosystem-python.md` — Textual (TCSS, reactive, workers, Pilot testing, `textual serve`), Rich, prompt_toolkit, Typer, questionary
- `ecosystem-typescript.md` — Ink (used by Claude Code, GitHub Copilot CLI, Gemini CLI), @clack/prompts, @inquirer/prompts, OpenTUI, color-library tradeoffs, argparse comparison
- `cli-basics.md` — `clig.dev` / 12-Factor / POSIX / XDG / `sysexits` synthesis for non-TUI CLIs
- `visual-patterns.md` — deep dive on the 7 layouts, borders, color tiers, semantic tokens, density, the clutter audit, responsive design (the breakpoint ladder + the floor), tables, status bars, progress, theming
- `interaction-patterns.md` — keybinding philosophies, focus management, the fzf/lazygit/k9s/helix patterns dissected, confirmation friction levels, undo/redo
- `exemplar-apps.md` — case studies of lazygit, k9s, btop, fzf, helix, yazi, atuin, htop, Posting, Harlequin, Claude Code, starship, and others

---

## When the skill triggers

Once installed, Claude will reach for this skill automatically when you ask about:

- **Building** a TUI or CLI ("build me a TUI for monitoring my docker containers")
- **Reviewing or refactoring** existing terminal UIs ("here's my Ratatui code, what's wrong with it?")
- **Library / framework choices** ("Bubble Tea vs Ratatui vs Textual vs Ink for a kanban app")
- **Specific design questions** ("how should I lay out a multi-pane git client", "should I support mouse")
- **Naming a known TUI app** as inspiration (lazygit, k9s, btop, helix, fzf, yazi, atuin)
- **Phrases like** "terminal app," "ncurses-style," "interactive shell tool," "CLI dashboard," "fzf-like picker"

---

## Example prompts

**Build:**
> "I want to build a TUI for monitoring my homelab — five docker hosts each running ~20 containers. I'd like to see CPU/mem/network at a glance and drill into any container's logs. I'm comfortable with Go and Rust. What would you build and how would you lay it out?"

**Review:**
> "Here's the layout of my Ratatui app: status bar at top with a progress bar, three panels horizontally split (file list 30%, diff 50%, commit log 20%), no footer. Keys are vim-style hjkl plus single letters. What's wrong with this from a UX perspective and what would you change?"

**Library decision:**
> "I'm starting a new TUI project in 2026 and torn between Bubble Tea, Ratatui, Textual, and Ink. It's a project management tool — kanban-board-style with multiple lists, drag-to-move, syncs to a backend, will be installed by ~5,000 internal users at our company. What would you pick and why?"

---

## Build

Every published release automatically gets a `tui-design.skill` asset attached by CI (see `.github/workflows/release.yml`), so the [latest release](https://github.com/gfargo/tui-design-skill/releases/latest) is the easiest source.

To build it yourself instead:

```bash
git clone https://github.com/gfargo/tui-design-skill.git
cd tui-design-skill
./scripts/package-skill.sh        # writes dist/tui-design.skill
```

The output is `dist/tui-design.skill` — a zip whose root is the `tui-design/` skill folder (`SKILL.md` + `references/`), ready to upload to Claude.ai. Only `bash` and `zip` are required.

---

## Repository layout

```
tui-design-skill/
├── .claude-plugin/
│   └── marketplace.json          # plugin marketplace catalog
├── .github/
│   └── workflows/
│       └── release.yml           # builds + attaches tui-design.skill on each release
├── scripts/
│   └── package-skill.sh          # builds dist/tui-design.skill locally
├── plugins/
│   └── tui-design/
│       ├── .claude-plugin/
│       │   └── plugin.json       # plugin manifest
│       └── skills/
│           └── tui-design/
│               ├── SKILL.md      # top-level skill (~300 lines)
│               └── references/
│                   ├── ecosystem-go.md
│                   ├── ecosystem-rust.md
│                   ├── ecosystem-python.md
│                   ├── ecosystem-typescript.md
│                   ├── cli-basics.md
│                   ├── visual-patterns.md
│                   ├── interaction-patterns.md
│                   └── exemplar-apps.md
├── evals/                        # reproducible eval sets (design-review + build-task)
│   ├── evals.json
│   └── build-evals.json
├── CHANGELOG.md
├── README.md
├── LICENSE
└── .gitignore
```

The nesting (`plugins/tui-design/skills/tui-design/`) is the official Claude Code plugin format. It looks redundant for a single-skill plugin but matches the schema and lets the marketplace infrastructure work uniformly.

---

## License

[MIT](./LICENSE) — use it, fork it, ship it.

## Contributing

Issues and pull requests welcome. Particularly useful contributions:

- **Fixes to ecosystem references** when libraries change (a new Bubble Tea or Lipgloss major, Ratatui adds new widgets, Textual ships new APIs)
- **New exemplar apps** worth studying with concrete lessons
- **Clarifications** where the skill's advice produced unexpected results in real use
- **Translations** of the skill into other languages

When opening a PR that changes the skill content, please describe the prompt you tested it on and what changed in the output.

## Acknowledgements

The principles in this skill draw on the public design wisdom of the Charm team (Bubble Tea, Lipgloss), the Ratatui maintainers, the Textual team at Textualize, the Ink maintainers, the [`clig.dev`](https://clig.dev) authors, and the many TUI authors whose apps are studied as exemplars within. The synthesis is mine; the design tradition is theirs.
