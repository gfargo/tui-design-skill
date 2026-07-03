# Exemplar apps — what makes specific TUIs great

Concrete case studies. When the user asks "how should I lay out my dashboard" or "how do I handle drilling into resources" or "what makes lazygit feel so good," point at one of these. Each entry covers: layout pattern, what it does well, specific features worth copying, lessons for builders.

For abstract principles, see `visual-patterns.md` and `interaction-patterns.md`. This file is the case-study companion.

## How to use this file

When the user asks about a design choice and you're unsure of the answer, find the analogous case here:

- "How should I lay out a dashboard?" → btop, bottom, htop.
- "How should drilling-down work?" → k9s, lazydocker.
- "How should I make searching fast?" → fzf, atuin.
- "How do I handle a million-row table?" → Harlequin, Toolong.
- "How should help/discovery work?" → htop's F-keys, helix's which-key, lazygit's footer.
- "How do I keep my AI chat smooth at high token rates?" → Claude Code, Copilot CLI (Ink + `<Static>`).
- "What's the spec for my undo system?" → lazygit's git-action stack.
- "How should mouse work in my TUI?" → btop (full mouse), helix (none), lazygit (augmentation).
- "How fast does my prompt picker need to be?" → fzf (<100ms), starship (<50ms).
- "What does a polished setup wizard look like?" → @clack/prompts (create-vite, create-astro) — see `ecosystem-typescript.md`.
- "How do I theme well?" → btop, bottom, helix, Posting (community palette support).

Concrete examples beat abstract principles for design questions. When in doubt, point at the app and the user can study its source.

**Entries, grouped:**
- Git: [lazygit](#lazygit-go-gocui) · [gitui](#gitui-rust-ratatui)
- Kubernetes / Docker: [k9s](#k9s-go-tview) · [lazydocker](#lazydocker-go-gocui)
- Monitors: [btop / btop++](#btop--btop-c-rust-clone-as-bottom) · [bottom / btm](#bottom--btm-rust-ratatui) · [htop](#htop-c-ncurses)
- Pickers and search: [fzf](#fzf-go) · [atuin](#atuin-rust-ratatui)
- Editors: [helix](#helix-rust-custom-renderer) · [neovim](#neovim-c--lua)
- File managers: [yazi](#yazi-rust-ratatui) · [ranger / lf / nnn / broot](#ranger--lf--nnn--broot-mostly-python-and-go)
- IDE-style apps: [Posting](#posting-python-textual) · [Harlequin](#harlequin-python-textual)
- Viewers: [Toolong](#toolong-python-textual) · [Glow](#glow-go-bubble-tea)
- Chat-style AI tools: [Claude Code / Copilot CLI / Gemini CLI](#claude-code-github-copilot-cli-gemini-cli-typescript-ink)
- CLI output discipline: [starship](#starship-rust-no-ui-framework) · [yt-dlp / aria2](#yt-dlp--aria2-cli-but-excellent-terminal-output)

---

## lazygit (Go, gocui)

> Multi-pane git client. The aesthetic that defined "lazy*."

**Layout:** persistent multi-panel — 5 panels on the left (Status, Files, Branches, Commits, Stash), 1 large panel on the right (Diff/details), command log strip at the bottom.

**What it does well:**
- **Numeric panel jumps** (`1`–`5`) feel instant and stay in muscle memory.
- **Context-sensitive single letters.** `c` commits in Files, checks out in Branches, copies in Stash. Works because the **footer hint bar updates per panel** — you always see what `c` does *now*.
- **Per-pane sub-tabs.** The Branches panel has Local / Remotes / Tags as `[`/`]` tabs.
- **Undo/redo for git operations** (`z` / `Ctrl+z`) — including rebases. This is unusually thoughtful for a TUI.
- **Subtle pulse animation** on background fetch — present without commanding attention.
- **Custom commands and aliases** in TOML config.

**Specific features worth copying:**
- The footer hint bar that updates per panel.
- Numeric panel jumps for >3 panels.
- A confirmation modal pattern that defaults to No.
- A "command log" pane showing what git commands actually ran (transparency).

**Lessons:** the cognitive load of "this letter means different things in different panels" is *worth it* if the footer always shows what's available. Trust users to read; help them see.

**Stack:** Go, gocui (jesseduffield's fork), TOML config.

---

## k9s (Go, tview)

> Kubernetes TUI. Drill-down stack + command mode.

**Layout:** drill-down stack with command-mode navigation. Top status header (cluster, context, namespace), main resource list, footer hints. Drill into a resource → full-screen detail view → `Esc` back.

**What it does well:**
- **Command mode** (`:pods`, `:svc`, `:ingress`) with **tab-completion and aliases**. Power users are stupendously fast.
- **Resource-aware actions:** `s` shells into a pod, `l` shows logs, `d` describes. Different resources get different actions.
- **Sortable columns** with `<` and `>`.
- **Fuzzy filter** (`/`) to narrow huge lists in real time.
- **Live updates** — pods change state; k9s reflects without refresh.
- **Plugin system** for custom actions (TOML).

**Specific features worth copying:**
- Command mode with tab-completion for any TUI with many "object types."
- Status-header showing the current "address" of where you are.
- Aliases (`po` for `pods`) — discoverable via `?`.
- Live updates with a debounced redraw (don't refresh on every event).

**Lessons:** when there are dozens of resource types, command mode beats menu navigation. But you must ship tab-completion and a discoverable alias list, or only the author will know what's possible.

**Stack:** Go, tview, YAML config, K8s client-go.

---

## btop / btop++ (C++; Rust clone as bottom)

> System monitor. The pinnacle of widget dashboard layouts.

**Layout:** widget dashboard. CPU graph (top-left), memory (top-right), network (bottom-left), processes table (bottom-right). All resizable, all rearrangeable, all configurable in TOML.

**What it does well:**
- **Truecolor gradient meters** that look genuinely beautiful.
- **Per-widget responsiveness** — CPU updates every 100ms, processes every 2s.
- **Mouse support** that doesn't get in your way (drag to resize, click to focus).
- **Theme system** with dozens of community themes.
- **Help modal (`h`)** that's actually informative, organized by widget.

**Specific features worth copying:**
- Widget independence (each owns its own update loop).
- Theme system as TOML — one file per theme.
- The decision to default to truecolor and degrade — most users have it now.

**Lessons:** in a dashboard, every widget should be independent — its own update cadence, its own scroll, its own focus. Don't synchronize what doesn't need to be.

**Stack:** C++ (btop), Rust (bottom — `btm`). Go's gotop pioneered the clone lineage, but cjbassi/gotop was archived in 2020 — the maintained fork is xxxserxxx/gotop; don't treat it as a current peer.

---

## fzf (Go)

> The fuzzy finder. Pattern-defining.

**Layout:** overlay/popup — appears over the shell, does one thing, exits.

**What it does well:**
- **Sub-100ms response** to every keystroke. This is *the* feature.
- **Match count visible** (`123/45678`).
- **Inline preview** with `--preview` — shows file contents, command output, anything.
- **Multi-select** with Tab.
- **Composable** — pipes to anywhere. `git branch | fzf | xargs git checkout` is the canonical pattern.
- **Smart-case** (lowercase = case-insensitive).

**Specific features worth copying:**
- The sub-100ms ceiling. If your filter is slower, profile until it isn't.
- The `--preview` pattern. Lets users see context without leaving the picker.
- Composability via stdin/stdout. Even your TUI can have a "summon fzf for picking" sub-flow.

**Lessons:** speed is a feature. Users summon fzf hundreds of times a day; making it 50ms instead of 200ms transforms the experience. Optimize for instantaneous feel.

**Stack:** Go, no UI framework — direct terminal manipulation.

---

## helix (Rust, custom renderer)

> Modal editor. Selection-first, multi-cursor first.

**Layout:** IDE three-panel — file explorer (toggleable; merged Jan 2025, navigate-only — no file management), main editor area (with multiple split views), bottom status + diagnostics. For most of its history helix had no tree at all — its identity was pickers instead of trees.

**What it does well:**
- **Selection-first modal editing.** `wd` selects-word-then-deletes (visual feedback before destructive action) vs vim's `dw`.
- **Multi-cursor as primary**, not an afterthought. `C` copies the selection to the next line (adding a cursor); selections can be split.
- **Tree-sitter** for syntax-aware text objects.
- **Space-based which-key.** Press `Space`, see a menu of `f` (file picker), `b` (buffer picker), `s` (symbols), etc.
- **`:` command mode** with completion.
- **Built-in LSP** (no plugins needed for most languages).

**Specific features worth copying:**
- Visual feedback before destructive action — highlight what you're about to operate on.
- Which-key popups for leader-key namespaces. Dramatically lowers the discovery barrier on modal apps.
- Single-binary distribution with sensible defaults — works out of the box.

**Lessons:** modes don't have to be confusing. Strong cursor-shape + status-bar mode indication + which-key for leaders make modal apps approachable.

**Stack:** Rust, custom rendering (Ratatui-adjacent).

---

## yazi (Rust, Ratatui)

> File manager with image preview. Miller columns.

**Layout:** miller columns — parent / current / preview, configurable widths (default `[1, 4, 3]`).

**What it does well:**
- **Async I/O everywhere.** Even directory listing is non-blocking. The UI never stalls.
- **Built-in image preview** via Sixel / kitty / iTerm2 (auto-detected).
- **Vim-style keybindings** with `:` command mode for less-common actions.
- **Plugins in Lua** — extends without recompile.
- **Tasks pane** for ongoing work (copies, transcodes).

**Specific features worth copying:**
- Async-everything — no operation should block the UI.
- The decision to support all three image protocols.
- Lua plugins for extension — extension without forking.

**Lessons:** in a file manager, *every* I/O can be slow on the wrong filesystem (network mounts, encrypted drives, dead USB). Async-first isn't optional; it's the foundation.

**Stack:** Rust, Ratatui, Crossterm, async via Tokio.

---

## atuin (Rust, Ratatui)

> Shell history with sync. Replaces Ctrl+R.

**Layout:** overlay/popup — replaces the default shell reverse-search with a richer fzf-style picker.

**What it does well:**
- **Replaces a built-in** (Ctrl+R) seamlessly. Users don't have to change muscle memory; they get a better version of what they already use.
- **Fuzzy filter with metadata** — when you ran the command, exit code, working directory, hostname.
- **Optional encrypted sync** to share history across machines.
- **Both CLI and TUI** from the same core. CLI for scripts (`atuin search`), TUI for interactive use.

**Specific features worth copying:**
- The "replace a familiar built-in" strategy. Far easier adoption than a new tool to learn.
- Showing metadata on every result (when, where, exit code) without cluttering.
- Dual CLI + TUI — the CLI handles scripts, the TUI handles exploration.

**Lessons:** the highest-leverage tools replace existing workflows rather than adding new ones. Users will switch to a slightly better Ctrl+R; they won't switch to a wholly new mental model.

Atuin Desktop (a GUI runbook app) launched in 2025; the CLI/TUI remains maintained alongside it.

**Stack:** Rust, Ratatui, optional self-hosted sync server.

---

## htop (C, ncurses)

> Process viewer. Old-school, still excellent.

**Layout:** persistent dense — header (CPU/mem/swap meters), process list (sortable), F-key strip at the bottom.

**What it does well:**
- **F-key strip** — `F1`–`F10` always visible at the bottom, telling you exactly what's available. The single most useful discoverability pattern.
- **Tree mode** (`F5`) — collapsible process tree.
- **Filter** (`F4`) and **search** (`F3`).
- **Color meters** in the header.
- **Mouse support** for clicking column headers to sort.

**Specific features worth copying:**
- The F-key strip. If you have 10 actions, just show them at the bottom — don't make users press `?` to discover them.
- Sortable column headers (click or key).
- Nice/renice via `F7`/`F8` — fast access to less-common but valuable actions.

**Lessons:** there's a reason htop has been the standard for 20 years. Persistent footer hints + sortable tables + mouse augmentation + keyboard primary = a recipe that just works. Sometimes the best design is the obvious one done well.

**Stack:** C, ncurses.

---

## bottom / btm (Rust, Ratatui)

> System monitor in Rust. The btop equivalent.

**Layout:** widget dashboard, configurable.

**What it does well:**
- **Tree process view** (`t`).
- **Battery widget** (laptops!).
- **Search and filter** in the process list.
- **Configurable layouts** via TOML — define rows and column ratios.
- **Per-widget basis** — focus a widget for full keyboard access.

**Specific features worth copying:**
- TOML layout config. Users will want to customize.
- Tree view as a single-key toggle.

**Lessons:** if you ship a dashboard, ship a way to rearrange it. Default layouts are never quite right for everyone.

**Stack:** Rust, Ratatui, Crossterm.

---

## Posting (Python, Textual)

> HTTP client. Postman-alternative for the terminal.

**Layout:** IDE three-panel — collection tree (left), request editor (main), response (bottom or right).

**What it does well:**
- **Empty states explain next action** — "No requests. Press `n` to create one."
- **Multiple themes** (Catppuccin, Gruvbox, Tokyo Night, Solarized, custom).
- **Vim and emacs editor key bindings** in text fields.
- **Response history** with diff between runs.
- **Variable substitution** (`{{token}}`) with environment switching.
- **Keyboard-first** — every action keyboard-reachable; mouse is augmentation.

**Specific features worth copying:**
- The empty-state pattern (`No X. Press `n` to create one.`) — never just say "No data."
- Theme switching at runtime.
- Both vim and emacs bindings in text fields — let users pick their muscle memory.

**Lessons:** Postman-style apps don't have to be GUIs. A well-designed TUI can replace bulky Electron apps and be faster, more keyboard-friendly, and offline-friendly.

**Stack:** Python, Textual, with `httpx` for HTTP.

---

## Harlequin (Python, Textual)

> SQL IDE. Database client + editor.

**Layout:** IDE three-panel — schema/catalog (left), SQL editor (top-right), results table (bottom-right).

**What it does well:**
- **Multi-adapter** — DuckDB, Postgres, MySQL, SQLite, Snowflake, BigQuery, Trino, all from the same UI.
- **Tree-sitter SQL** highlighting in the editor.
- **Fast result virtualization** for million-row queries.
- **Run-on-keystroke** option for ad-hoc exploration.
- **Snippets** and history.

**Specific features worth copying:**
- The plugin/adapter pattern (clean abstraction → swap database backend).
- Result virtualization for huge tables.
- The decision to support both modal and modeless input in the editor.

**Lessons:** when your TUI is a productivity tool, take performance seriously. Million-row results require real virtualization, not "render the first 1000."

**Stack:** Python, Textual, with `textual-fastdatatable` for performance.

---

## ranger / lf / nnn / broot (mostly Python and Go)

> File managers. The miller-columns lineage.

**Layout:** miller columns (parent / current / preview).

**What they do well:**
- **Vim-style navigation** (`hjkl`).
- **Bookmarks** (`m{a-z}`, `'{a-z}`).
- **Image preview** in the right column (terminal-graphics or ASCII).
- **Composable with shell** — `ranger --choosefile=/tmp/path` for "use ranger to pick a file in scripts."
- **Each handles a different niche:**
  - **ranger** — Python, mature, lots of features, slower startup.
  - **lf** — Go, very fast, minimal.
  - **nnn** — C, the fastest, most minimal.
  - **broot** — Rust, tree-mode + fuzzy filter at the same time.

**Lessons:** for browsing tools, startup time matters as much as a fancy UI. nnn opens in single-digit ms; ranger takes a noticeable beat. Both have devoted users; performance is a real axis to compete on.

---

## gitui (Rust, Ratatui)

> Git TUI in Rust.

**Layout:** persistent multi-panel, similar to lazygit but Rust-based.

**What it does well:**
- **Fast, even on huge repos.** Async git operations.
- **Diff viewer** with syntax highlighting.
- **Async fetch with no UI block.**
- **Push/pull progress** rendered in-app.

**Specific features worth copying:**
- The pattern of running git operations on a worker thread and posting progress events back.
- Showing diff with proper syntax highlighting (Tree-sitter or syntect).

**Lessons:** git operations on huge repos can be slow. If your tool wraps git, the user experience hinges on whether you keep the UI responsive. Threading-pool with progress events is the pattern.

**Stack:** Rust, Ratatui, `git2` library.

---

## lazydocker (Go, gocui)

> Docker TUI. Same paradigm as lazygit.

**Layout:** persistent multi-panel — sidebar with Project / Containers / Images / Volumes / Networks, main panel showing details (Logs / Stats / Env / Config / Top tabs).

**What it does well:**
- **Tabbed-within-panel** in the main panel — `[`/`]` cycle Logs/Stats/Env/Config/Top.
- **Live log streaming** with auto-scroll toggle.
- **Resource graphs** (CPU / memory / network) in the Stats tab.
- **Custom commands** in YAML config.

**Lessons:** if you're building a "lazy*" tool for some other domain (kubernetes, AWS, your CI system), this template works. Persistent sidebar + main panel with tabs + per-context single letters + footer hint bar.

**Stack:** Go, gocui (jesseduffield's fork).

---

## neovim (C + Lua)

> Editor. The most-customized TUI in existence.

**Why study:** the *plugin* and *config* ecosystem teaches lessons about extensibility. Every successful neovim plugin (telescope.nvim, which-key.nvim, lualine.nvim, nvim-tree.lua, lazy.nvim) demonstrates a UI pattern worth knowing:

- **telescope.nvim** — fuzzy picker for everything (files, buffers, LSP symbols, git refs). The "picker for X" pattern generalizes.
- **which-key.nvim** — popup showing available leader-key follow-ups. Discoverability by default.
- **lualine.nvim** — status line as a configurable component pipeline. Mode + git branch + diagnostics + filename + position.
- **nvim-tree.lua** — file tree sidebar with vim navigation.
- **lazy.nvim** — plugin manager with lazy-loading. Cold-start matters.

**Lessons:** the design choices in vim — modal editing, leader keys, command mode, registers, marks, buffers, splits — have proven robust over decades. Even non-editor TUIs benefit from borrowing these mental models when they fit.

**Stack:** C (core), Lua (config and plugins).

---

## Toolong (Python, Textual)

> Log viewer for multi-GB files.

**Layout:** single panel (the log) with optional filter sidebar.

**What it does well:**
- **Virtualization for multi-GB files.** Doesn't load the whole file.
- **Real-time tailing** with `-f`-style follow.
- **Regex filter** that doesn't slow down on huge files.
- **Merge multiple log files** by timestamp.
- **Pretty syntax highlighting** for common log formats (JSON, syslog, NGINX).

**Lessons:** when working with potentially-huge data, virtualization is the difference between "it works on my 10MB sample" and "it works in production on 50GB rotated logs." Plan for it from day one.

**Stack:** Python, Textual.

---

## Glow (Go, Bubble Tea)

> Markdown reader for the terminal.

**Layout:** single panel (the rendered Markdown) with optional file picker.

**What it does well:**
- **Beautiful Markdown rendering** via Glamour.
- **Multiple themes** (light, dark, custom JSON).
- **Local + remote files** (GitHub URLs work directly).
- **Stash** — save documents from any source.

**Specific features worth copying:**
- The decision to ship as both a CLI (`glow README.md` pipes to terminal) and a TUI (`glow` opens the picker).
- Glamour's themes as JSON — define style once, apply everywhere.

**Stack:** Go, Bubble Tea, Glamour.

---

## Claude Code, GitHub Copilot CLI, Gemini CLI (TypeScript, Ink)

> AI coding assistants in the terminal.

**Layout:** chat-like — input at the bottom, scrolling output above.

**What they do well:**
- **Streaming text rendering** without flicker (use `<Static>` for finalized history).
- **Status indicators** (thinking, tool-use, error states) without overwhelming.
- **Inline diff rendering** for code changes.
- **`/`-prefixed slash commands** for actions (clear, model switch, etc.).
- **Shell integration** — paste files, run commands, read working directory.

**Lessons:** for any streaming/chat-like TUI, the architecture is "append-only history above + interactive input below." Use `<Static>` (or equivalent) for the history so finalized turns don't re-render. This is what lets these apps stay smooth at high token rates.

**Stack:** TypeScript, Ink, React, Yoga.

---

## starship (Rust, no UI framework)

> Cross-shell prompt.

**Why study:** not technically a TUI, but the **performance discipline** is exemplary. Starship runs on every prompt; it has to start in <50ms or users feel it.

**What it does well:**
- **Sub-50ms cold start** as a hard requirement. Every feature added must not blow the budget.
- **Async git status** — checks asynchronously, displays placeholder while waiting.
- **Minimal allocations.** Profiles every release.
- **Single TOML config** with semantic blocks (one per "module": `[character]`, `[directory]`, `[git_branch]`).
- **Cross-shell** — bash, zsh, fish, pwsh, ion, nu — all from one binary.

**Lessons:** for any tool that runs frequently (shell prompts, file pickers, fuzzy finders), startup time is a feature. Profile, optimize, never regress. Users feel 100ms even if they can't articulate it.

**Stack:** Rust, no UI framework — direct ANSI emission.

---

## yt-dlp / aria2 (CLI, but excellent terminal output)

> Downloaders.

**Why study:** great example of progress UI in non-TUI tools. They show:
- **Multi-stream progress** (parallel downloads, all visible).
- **Adaptive output** — full progress bars on TTY, simple percentage on CI.
- **Final summary** at the end (success / failed counts, total size).

**Lessons:** even non-interactive CLIs benefit from thoughtful output design. Show progress, show summary, degrade for non-TTY.
