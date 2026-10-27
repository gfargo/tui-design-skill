# Exemplar apps — what makes specific TUIs great

Concrete case studies for design questions ("how should I lay out my dashboard?", "what makes lazygit feel so good?"). Each entry has four parts: **Layout** (the shape), **Copy this** (specific features worth stealing), **Lesson** (what transfers), and **Cite when** (the question that should send you here). Point at the app so the user can study its source. The abstract rules live in `visual-patterns.md`, `interaction-patterns.md`, and `cli-basics.md`; this file is the case-study companion and owns only app-specific facts.

**Contents:**
- Git and Docker: [lazygit (with gitui and lazydocker)](#lazygit-go-gocui)
- Kubernetes: [k9s](#k9s-go-tview)
- Monitors: [btop (with bottom)](#btop-c-with-bottom) · [htop](#htop-c-ncurses)
- Pickers and search: [fzf](#fzf-go) · [atuin](#atuin-rust-ratatui)
- Editors: [helix](#helix-rust-custom-renderer)
- File managers: [yazi (with ranger, lf, nnn, broot)](#yazi-rust-ratatui)
- IDE-style apps and viewers: [Posting](#posting-python-textual) · [Harlequin and Toolong](#harlequin-and-toolong-python-textual)
- Chat-style AI tools: [Claude Code / Copilot CLI / Gemini CLI](#claude-code-github-copilot-cli-gemini-cli-typescript)
- Output discipline: [starship](#starship-rust-no-ui-framework)

## App → lesson → when to cite

| App | Lesson | Cite when |
|---|---|---|
| lazygit | Persistent multi-panel, context-sensitive letters, scoped git undo | Multi-pane layouts, an undo spec, a "lazy*" tool for another domain, mouse as augmentation |
| k9s | Drill-down stack, resource-aware actions, instant filter | Drilling into resources, live-updating lists |
| btop | Independent widgets, truecolor with degradation, theme files, mouse as augmentation | Dashboard layout, theming, mouse support |
| htop | Always-visible F-key strip | Help and discovery |
| fzf | Speed is the feature; bounded inline picker | Search latency, picker design, summoning a picker from a TUI |
| atuin | Replace a familiar built-in | Adoption strategy, inline picker height |
| helix | Mode visible in the statusline; pickers instead of trees | Modal editing, which-key, mode cues |
| yazi | Async everything; sibling file managers compete on startup | File managers, slow filesystems |
| Posting | Empty states name the next action; jump mode | IDE-style three-panel apps, theming |
| Harlequin, Toolong | Virtualize from day one | Million-row tables, multi-GB logs |
| Claude Code, Copilot CLI, Gemini CLI | Inline append-only versus alt screen with a virtualized transcript | Chat UIs at high token rates |
| starship | Startup time is a budget | Anything run on every prompt |

Related pickers: `@clack/prompts` (create-vite; create-astro has the same look via its own `@astrojs/cli-kit`) is the polished setup-wizard reference; see `ecosystem-typescript.md`.

---

## lazygit (Go, gocui)

> Multi-pane git client. The aesthetic that defined "lazy*."

**Layout:** persistent multi-panel: 5 left panels (Status, Files, Branches, Commits, Stash), one large right panel (diff/details), a command log strip at the bottom. Panels carry sub-tabs on `[`/`]` (Branches: Local / Remotes / Tags). Go, gocui (jesseduffield's fork, copied into the repo as `pkg/gocui` in April 2026) on tcell v3.

**Copy this:**
- **Undo/redo** (`z` / `Z`), driven by the reflog: it can walk back a rebase, but not working-tree or stash changes, pushes, or branch creation, and not while a rebase is in progress.
- A **command log** showing the git commands that actually ran (transparency).
- Confirmation popups for destructive actions (Enter confirms, Esc cancels).
- A small spinner for background fetch: present without commanding attention.
- Custom commands and aliases in YAML config (`config.yml`).

**Lesson:** the numeric-panel-jump + context-sensitive-letter interaction is dissected in `interaction-patterns.md` → *The lazygit pattern — multi-pane with numeric tabs*. Two siblings show how far the template travels:
- **lazydocker** (Go, gocui): same paradigm, a sidebar (Project / Containers / Services / Images / Volumes / Networks) plus a main panel with `[`/`]` tabs (Logs / Stats / Env / Config / Top), live log streaming with an auto-scroll toggle, and resource graphs in Stats. For a "lazy*" tool in another domain (Kubernetes, AWS, your CI system), use persistent sidebar + tabbed main panel + per-context single letters + footer hint bar.
- **gitui** (Rust, Ratatui, `git2` plus `gix`): fast on huge repos, with async git operations: work runs on a worker thread that posts progress events back (fetch, push, and pull progress render in-app) so the UI stays responsive. If your tool wraps git, the experience hinges on that.

**Cite when:** laying out a multi-pane app, specifying undo, building a lazy* tool for another domain, or wrapping git.

---

## k9s (Go, tview)

> Kubernetes TUI. Drill-down stack + command mode.

**Layout:** drill-down stack with command-mode navigation: a top status header (cluster, context, namespace), the main resource list, footer hints. Drill into a resource for a full-screen detail view, `Esc` back. Go, derailed's forks of tview and tcell, K8s client-go.

**Copy this:**
- **Resource-aware actions:** `s` shells into a pod, `l` shows logs, `d` describes; different resources get different actions.
- **Sortable columns** via Shift+letter (`shift-n` name, `shift-a` age, `shift-o` the selected column).
- **Instant filter** (`/`) narrows huge lists in real time: regex by default, `/-f` switches to fuzzy matching.
- **Live updates** without manual refresh, via a debounced redraw (don't refresh on every event).
- A status header showing the current "address" of where you are; a plugin system for custom actions (`plugins.yaml`).

**Lesson:** the ex-command mode (`:pods`, `:svc`, tab-completion, aliases) is dissected in `interaction-patterns.md` → *The k9s pattern — command-driven*.

**Cite when:** designing drill-down into resources, live-updating lists, or a command-driven navigation layer.

---

## btop (C++), with bottom

> System monitor. The pinnacle of widget dashboard layouts.

**Layout:** widget dashboard. CPU graph full-width on top; memory above network on the left; processes table on the right. Boxes can be toggled, swapped to alternate positions, and saved as presets (not drag-resized), all configured in `btop.conf` (a TOML-like `key = value` file).

**Copy this:**
- **Truecolor gradient meters**, defaulting to truecolor and degrading.
- **One tunable refresh rate** (`update_ms`, default 2000) shared by every box; each box keeps its own scroll, focus, and graph history.
- **Mouse that doesn't get in the way:** highlighted keys and boxes are clickable, lists scroll with the wheel, no drag-resize to fight.
- **Themes** as one `.theme` file per theme (a simple `theme[key]="#hex"` format), with dozens of community themes.
- A **help modal** (`h`, `?`, or F1) organized by widget.
- **bottom / btm** (Rust, Ratatui; inspired by gtop, gotop, and htop rather than by btop): layout defined in TOML rows and column ratios, a tree process view as a single-key toggle (`t`), a battery widget, process search and filter, and per-widget focus for full keyboard access.

**Lesson:** every widget should be independent: its own scroll, focus, and data source. Share a refresh clock when the data sources are cheap and uniform (btop does); give a widget its own cadence only when its source is slow or expensive. If you ship a dashboard, ship a way to rearrange it, since default layouts are never right for everyone. cjbassi/gotop was archived in 2020; the maintained fork is xxxserxxx/gotop, so don't cite the original as a current peer.

**Cite when:** laying out a dashboard, theming, or deciding how mouse should work (btop clickable keys and boxes; helix keyboard-first; lazygit augmentation).

---

## htop (C, ncurses)

> Process viewer. Old-school, still excellent.

**Layout:** persistent dense: header (CPU/mem/swap meters), sortable process list, F-key strip at the bottom.

**Copy this:**
- **F-key strip:** `F1`–`F10` always visible at the bottom. If you have 10 actions, show them rather than making users press `?` to discover them.
- Tree mode (`F5`), filter (`F4`), search (`F3`); nice/renice on `F7`/`F8` keep less-common but valuable actions one key away.
- Sortable column headers (click or key); color meters in the header.

**Lesson:** persistent footer hints + sortable tables + mouse augmentation + keyboard primary is a recipe that just works.

**Cite when:** designing help and discovery (footer rules are in `visual-patterns.md` → *Footer hint bar*).

---

## fzf (Go)

> The fuzzy finder. Pattern-defining.

**Layout:** full-screen by default; `--height` opts into a bounded picker below the cursor. Either form does one thing and exits. Go, no UI framework: its own renderer on Unix, tcell on Windows.

**Copy this:**
- **Preview pane** (`--preview`): file contents or command output without leaving the picker.
- **Composable:** `git branch | fzf | xargs git checkout` is the canonical pattern; even a full TUI can have a "summon fzf for picking" sub-flow.
- Opens `/dev/tty` for its interactive UI while keeping the selected value on stdout. Use `--height` when shell context must remain visible; see `visual-patterns.md` → *Inline, alt-screen, or overlay*.

**Lesson:** speed is a feature. Users summon fzf hundreds of times a day; 50ms instead of 200ms transforms the experience. The instant-fuzzy-filter interaction (sub-100ms updates, match count, smart-case, ranking) is dissected in `interaction-patterns.md` → *The fzf pattern in detail*.

**Cite when:** designing search latency or a picker.

---

## atuin (Rust, Ratatui)

> Shell history with sync. Replaces Ctrl+R.

**Layout:** inline, capped at `inline_height` (default 40 lines; `0` = full screen): the same bounded model as fzf `--height`, not an overlay. It replaces the default shell reverse-search with a richer fzf-style picker.

**Copy this:**
- **Replace a familiar built-in** (Ctrl+R) so users keep their muscle memory and get a better version of what they already use.
- **Metadata on every result** (when you ran it, exit code, working directory, hostname) without clutter, plus optional encrypted sync across machines.
- **CLI and TUI from the same core:** the CLI for scripts (`atuin search`), the TUI for interactive use.

**Lesson:** the highest-leverage tools replace existing workflows rather than adding new ones; users will switch to a slightly better Ctrl+R, not to a wholly new mental model.

**Cite when:** choosing an adoption strategy or the height of an inline picker.

---

## helix (Rust, custom renderer)

> Modal editor. Selection-first, multi-cursor first.

**Layout:** main editor area (with multiple split views) plus a bottom statusline and diagnostics; everything else arrives as a picker. Even its file explorer (`Space e`, released in 25.07) is a directory-browsing picker, not a persistent sidebar tree: helix's identity is pickers instead of trees.

**Copy this:**
- **Space-based which-key:** press `Space`, see a menu of `f` (file picker), `b` (buffer picker), `s` (symbols), etc.
- A `:` command mode with completion; tree-sitter for syntax-aware text objects; built-in LSP, so most languages need no plugins.
- **Mouse:** on by default but never required (keyboard-first).

**Lesson:** modes don't have to be confusing. helix shows the mode in the statusline (`NOR`/`INS`/`SEL`) plus which-key for leaders. By default the cursor is a block in every mode and `color-modes` is off, so per-mode cursor shapes and colors are opt-in config (`[editor.cursor-shape]`, `color-modes = true`): worth enabling, and worth shipping on by default in your own modal app. Selection-first editing and multi-cursor-as-primary are dissected in `interaction-patterns.md` → *The helix pattern — selection-first modal editing*.

**Cite when:** designing a modal app, which-key discovery, or mode cues.

---

## yazi (Rust, Ratatui)

> File manager with image preview. Miller columns.

**Layout:** miller columns (parent / current / preview), configurable widths (default `[1, 4, 3]`). Layout details are in `visual-patterns.md`.

**Copy this:**
- **Async I/O everywhere**, even directory listing; the UI never stalls. A tasks pane shows ongoing work (copies, transcodes).
- **Built-in image preview** via Sixel / kitty / iTerm2 (auto-detected), supporting all three protocols.
- **Vim-style keybindings**, with `;` / `:` to run a shell command (`:` blocks until it finishes).
- **Lua plugins**: extension without recompiling or forking.

**Lesson:** every I/O can be slow on the wrong filesystem (network mounts, encrypted drives, dead USB), so async-first is the foundation, not an option.

**Siblings:** ranger (Python, mature, many features, slower startup), lf (Go, very fast, minimal), nnn (C, fastest and most minimal), broot (Rust, tree mode + fuzzy filter at once). All share vim-style `hjkl`, bookmarks, and shell composability (`ranger --choosefile=/tmp/path`); the cd-on-exit wrapper is in `cli-basics.md`. For browsing tools, startup time is a real axis to compete on.

**Cite when:** designing a file manager or anything that touches slow filesystems.

---

## Posting (Python, Textual)

> HTTP client. Postman-alternative for the terminal.

**Layout:** IDE three-panel: collection tree (left), request editor (main), response (bottom or right).

**Copy this:**
- **Empty states that name the next action:** an empty collection says "Collection is empty. Press ctrl+s to save the current request." (the pattern is in `visual-patterns.md` → *States*).
- **Jump mode:** label every focusable widget with a letter so a keyboard user never tabs through a form; plus vim keys.
- **Runtime theme switching** (Catppuccin, Gruvbox, Tokyo Night, Solarized, custom).
- Import/export of curl commands, Postman collections, and OpenAPI specs; `{{token}}` variable substitution with environment switching.

**Lesson:** Postman-style apps don't have to be GUIs; a keyboard-first TUI can be faster and offline-friendly. This is the released Posting 2.x line (Python, Textual, `httpx`); `main` now holds Posting 3, a Go rewrite, so cite Posting 2 when you need a Textual example.

**Cite when:** designing an IDE-style three-panel app, empty states, jump navigation, or runtime theming.

---

## Harlequin and Toolong (Python, Textual)

> Harlequin: SQL IDE. Toolong: log viewer for multi-GB files.

**Layout:** Harlequin is an IDE three-panel: schema/catalog (left), SQL editor (top-right), results table (bottom-right). Toolong is a single panel (the log) with an optional filter sidebar.

**Copy this:**
- **Result virtualization** for million-row queries (Harlequin, with `textual-fastdatatable`) and for multi-GB files that are never loaded whole (Toolong).
- Toolong: real-time tailing (`-f`-style follow), a regex filter that stays fast on huge files, merging multiple logs by timestamp, highlighting for common formats (JSON, syslog, NGINX).
- Harlequin: a clean adapter abstraction (DuckDB, SQLite, Postgres, MySQL/MariaDB, and ODBC from the maintainers, plus community adapters), tree-sitter SQL highlighting, and searchable query history (`F8`).

**Lesson:** with potentially huge data, "render the first 1000" fails in production; virtualize from day one, the difference between a 10MB sample and 50GB rotated logs. Toolong has had no release since April 2024: study it for the design, not as a maintained dependency.

**Cite when:** designing a million-row table or a large-file viewer.

---

## Claude Code, GitHub Copilot CLI, Gemini CLI (TypeScript)

> AI coding assistants in the terminal.

**Layout:** chat-like: transcript above, input pinned at the bottom. Two render models, both shipping:
- **Inline, append-only:** Gemini CLI's default and Claude Code's classic renderer. Finalized turns go to native scrollback (Ink's `<Static>` or an equivalent), so the terminal's own scrollback, search, and copy work for free. The cost grows with the transcript: long streaming sessions can flicker, jump the scroll position, and grow memory.
- **Alternate screen with a virtualized transcript:** Claude Code's fullscreen renderer (a research preview; the default for users who first ran Claude Code on or after May 6, 2026; `/tui` switches) and Copilot CLI (default since 1.0.8, no opt-out since 1.0.12). Only visible messages render, so memory stays flat and nothing flickers. The cost: the app must rebuild what the terminal gave for free (search, copy, exporting the transcript to scrollback) and keep an inline fallback. Claude Code forces its classic renderer in screen-reader mode.

**Copy this:** status indicators (thinking, tool use, error) that don't overwhelm; inline diff rendering for code changes; `/`-prefixed slash commands; shell integration (paste files, run commands, read the working directory).

**Lesson:** a chat TUI is something users live in, so it faces the same choice as any app (`visual-patterns.md` → *Inline, alt-screen, or overlay*). Inline with `<Static>` for finalized turns is the simpler start. Move to the alternate screen with a virtualized transcript when sessions run long, and ship search, copy, scrollback export, and an inline or accessible fallback with it. Ink's README lists all three as users, and Gemini CLI renders with a fork of Ink (React, Yoga); the internals of Claude Code's and Copilot CLI's alternate-screen renderers aren't documented.

**Cite when:** a chat or agent UI must stay smooth at high token rates.

---

## starship (Rust, no UI framework)

> Cross-shell prompt: not a TUI, but a performance exemplar.

**Layout:** none; direct ANSI emission from a single binary, configured by one TOML file with a block per module (`[character]`, `[directory]`, `[git_branch]`).

**Copy this:** per-module time budgets instead of a single startup number, so a module that overruns is dropped from that prompt with a warning instead of delaying it. The numbers (`scan_timeout`, `command_timeout`) are in `cli-basics.md` → *Startup time*.

**Lesson:** for any tool that runs frequently (shell prompts, pickers, fuzzy finders), startup time is a feature; users feel 100ms even if they can't articulate it.

**Cite when:** setting a startup or per-module latency budget.
