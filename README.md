# tui-design

[![Release](https://img.shields.io/github/v/release/gfargo/tui-design-skill?label=release&color=2da44e)](https://github.com/gfargo/tui-design-skill/releases)
[![Skills](https://www.skills.sh/b/gfargo/tui-design-skill)](https://www.skills.sh/gfargo/tui-design-skill)
[![Validate](https://github.com/gfargo/tui-design-skill/actions/workflows/validate.yml/badge.svg)](https://github.com/gfargo/tui-design-skill/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An agent skill for designing and building **clean, professional, minimal terminal UI (TUI) applications and command-line tools** — for Codex, Claude, and compatible skill-aware agents, across Go, Rust, Python, and TypeScript.

Use it for greenfield builds, design reviews, refactors, library decisions, and "should I use Bubble Tea or Ratatui?"-class questions. Covers the universal patterns (layouts, color, keybindings, discoverability) plus per-ecosystem deep-dives for Bubble Tea, Ratatui, Textual, and Ink.

**[What it covers](#what-the-skill-covers) · [When it triggers](#when-the-skill-triggers) · [Example prompts](#example-prompts) · [Install](#install) · [Build](#build) · [Evaluate](#evaluation) · [Repo layout](#repository-layout) · [Contributing](#contributing)**

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

## What the skill covers

The skill uses progressive disclosure: its 139-line `SKILL.md` carries the workflow, routing table, and cross-cutting contracts, then loads one authoritative reference per topic on demand. The nine Markdown files total about 4,160 lines, but the agent does not need all of that context for every question.

**Top-level (`SKILL.md`):**
- Product classification: one-shot CLI, summon–choose–exit tool, or full-screen session
- Single-source routing for layouts, visual systems, interactions, ecosystem APIs, CLI contracts, and case studies
- Two reflexes applied to every layout review — the **clutter audit** (make "feels busy" countable) and **pressure-test the floor** (responsive behavior at 80×24 and narrower), even when the user didn't ask about them
- Cross-cutting contracts for lifecycle, non-blocking work, redraws, cell width, output streams, semantic color, keyboard access, and plain-mode fallbacks
- A build workflow, bottom-heavy test pyramid, verification matrix, and prioritized review checklist

**References (loaded as needed):**
- `ecosystem-go.md` — Bubble Tea, Lipgloss, Bubbles, Huh, tview, gocui, Cobra, Wish, gum
- `ecosystem-rust.md` — Ratatui, Crossterm, color-eyre panic safety, Cursive, clap, cliclack, async with Tokio
- `ecosystem-python.md` — Textual (TCSS, reactive, workers, Pilot testing, `textual serve`), Rich, prompt_toolkit, Typer, questionary
- `ecosystem-typescript.md` — Ink (used by Claude Code, GitHub Copilot CLI, Gemini CLI), @clack/prompts, @inquirer/prompts, OpenTUI, color-library tradeoffs, argparse comparison
- `cli-basics.md` — `clig.dev` / 12-Factor / POSIX / XDG / `sysexits` synthesis for non-TUI CLIs, plus shell integration hooks, shipping/update/telemetry etiquette, and first-run auth flows
- `visual-patterns.md` — deep dive on the 7 layouts, inline vs alt-screen (and the receipt-pattern exit contract), borders, color tiers, semantic tokens, density, the clutter audit, responsive design (the breakpoint ladder + the floor), tables, status bars, progress, disconnected/timeout states, theming, Nerd Font icon conventions
- `interaction-patterns.md` — keybinding philosophies, focus management, forms and settings-screen design, OSC 8/52/9 (hyperlinks, clipboard-over-SSH, notifications), the fzf/lazygit/k9s/helix patterns dissected, confirmation friction levels, undo/redo
- `exemplar-apps.md` — case studies of lazygit, k9s, btop, fzf, helix, yazi, atuin, htop, Posting, Harlequin, Claude Code, starship, and others

---

## When the skill triggers

Once installed, a compatible agent can reach for this skill automatically when you ask about:

- **Building** a TUI or CLI ("build me a TUI for monitoring my docker containers")
- **Reviewing or refactoring** existing terminal UIs ("here's my Ratatui code, what's wrong with it?")
- **Library / framework choices** ("Bubble Tea vs Ratatui vs Textual vs Ink for a kanban app")
- **Specific design questions** ("how should I lay out a multi-pane git client", "should I support mouse")
- **Naming a known TUI app** as inspiration (lazygit, k9s, btop, helix, fzf, yazi, atuin)
- **Phrases like** "terminal app," "ncurses-style," "interactive shell tool," "CLI dashboard," "fzf-like picker"

It stays out of browser/web UI, native GUI, editor/font configuration, and backend or shell work when no terminal interface is part of the request.

---

## Example prompts

**Build:**
> "I want to build a TUI for monitoring my homelab — five docker hosts each running ~20 containers. I'd like to see CPU/mem/network at a glance and drill into any container's logs. I'm comfortable with Go and Rust. What would you build and how would you lay it out?"

**Review:**
> "Here's the layout of my Ratatui app: status bar at top with a progress bar, three panels horizontally split (file list 30%, diff 50%, commit log 20%), no footer. Keys are vim-style hjkl plus single letters. What's wrong with this from a UX perspective and what would you change?"

**Library decision:**
> "I'm starting a new TUI project in 2026 and torn between Bubble Tea, Ratatui, Textual, and Ink. It's a project management tool — kanban-board-style with multiple lists, drag-to-move, syncs to a backend, will be installed by ~5,000 internal users at our company. What would you pick and why?"

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

The pinned CLI below requires Node.js 22.20 or newer. It auto-detects compatible agents, but the examples name the target explicitly so the destination is unambiguous:

```bash
# Install for Claude Code in the current project
npx --yes skills@1.5.22 add gfargo/tui-design-skill -a claude-code

# Install into Claude Code's global skill directory
npx --yes skills@1.5.22 add gfargo/tui-design-skill -a claude-code -g

# Install for another agent
npx --yes skills@1.5.22 add gfargo/tui-design-skill -a cursor
npx --yes skills@1.5.22 add gfargo/tui-design-skill -a codex

# List skills installed via npx skills
npx --yes skills@1.5.22 list

# Update later
npx --yes skills@1.5.22 update tui-design
```

`npx skills` discovers this skill via the same `marketplace.json` used by Option A. `-g` means the selected agent's global skill directory; the exact path depends on that agent. Upgrade the pinned CLI deliberately after checking its Node requirement and install behavior.

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

## Build

Every published release automatically gets a `tui-design.skill` asset attached by CI (see `.github/workflows/release.yml`), so the [latest release](https://github.com/gfargo/tui-design-skill/releases/latest) is the easiest source.

To build it yourself instead:

```bash
git clone https://github.com/gfargo/tui-design-skill.git
cd tui-design-skill
./scripts/package-skill.sh        # writes dist/tui-design.skill
```

The output is `dist/tui-design.skill`—a deterministic zip containing the exact ten-file `tui-design/` allowlist (`SKILL.md`, `agents/openai.yaml`, and eight references), ready to install in a compatible agent. Packaging rejects symlinks, generated files, caches, and undeclared resources. It requires Bash, `zip`, `unzip`, and the common GNU/BSD forms of `find`, `cp`, `chmod`, `touch`, and `mktemp`. Run `./scripts/validate-release.sh` to validate manifests, Codex metadata, the core-size and duplication budgets, Markdown structure, eval JSON and harness tests, archive integrity, and repeatable output; that validator also requires Python 3.9 or newer.

## Evaluation

The committed eval sets contain prompts and assertion rubrics. `scripts/eval_harness.py` turns them into auditable runs while staying provider-neutral: the runner command reads a prompt from stdin and writes one response to stdout, and it is invoked directly without a shell.

```bash
# Run the same set without skill injection.
python3 scripts/eval_harness.py run \
  --eval-set evals/v151-correction-evals.json \
  --condition baseline --provider "provider-name" --model "exact-model-id" \
  --runner-version "runner 1.2.3" --repeat 2 \
  -- path/to/model-runner --its-arguments

# Run it with a clean-context instruction pointing at this skill.
python3 scripts/eval_harness.py run \
  --eval-set evals/v151-correction-evals.json \
  --condition with-skill --provider "provider-name" --model "exact-model-id" \
  --runner-version "runner 1.2.3" --temperature 0 --repeat 2 \
  -- path/to/model-runner --its-arguments
```

Each schema-v3 `run.json` declares a machine-readable schema URI and records the caller-supplied exact provider/model identifiers, runner version, exposed seed and temperature, system-prompt status or hash, repetitions, runner executable name and argv hash, git commit and dirty state, host metadata, eval-set and skill hashes, prompt and response hashes, timings, exit codes, and raw artifact paths. Use `--system-prompt-file` to record only a known prompt's SHA-256 and byte length, `--no-system-prompt` when there truly is none, or neither when the runner does not expose it. Exact runner arguments are private by default; add `--record-runner-argv` only when they contain no credentials or signed URLs and the evidence needs full command reproduction. Generated work stays under ignored `evals/runs/`; copy only reviewed evidence intended for the repository into `evals/results/`. Keep credentials in the runner's environment.

Grades are a separate schema-v3 JSON artifact with a grader kind, name, prompt version and SHA-256, plus one ordered boolean result per rubric assertion and trial. Model graders also record provider, model, runner version, and generation metadata. The scoring command reconstructs the complete expected trial set from the eval source and rejects missing trials or assertions before calculating aggregate and per-case pass rates. Summary validation requires the grades and recomputes every aggregate rather than trusting recorded totals:

```bash
python3 scripts/eval_harness.py score \
  --run evals/runs/RUN_ID/run.json \
  --grades evals/runs/RUN_ID/grades.json

python3 scripts/eval_harness.py validate \
  --run evals/runs/RUN_ID/run.json \
  --grades evals/runs/RUN_ID/grades.json \
  --summary evals/runs/RUN_ID/summary.json \
  --require-completed
```

Use `--prepare-only` when the model interface cannot be called as a command; it still generates the exact baseline or with-skill prompts and records the intended provider and model. The validator continues to accept schema-v2 artifacts; revalidate historical evidence from the clean source commit recorded in its `run.json` when eval or skill inputs have since changed. See [`evals/README.md`](evals/README.md), `python3 scripts/eval_harness.py --help`, and the integration tests for the complete artifact contract.

The reviewed v1.6.1 evidence under `evals/results/v1.6.1-forward-test/` is a complete single-snapshot run of all seven correction cases: 25/25 assertions with exact provider, model, runner, source commit, skill hash, raw outputs, grades, and summary recorded. Trigger-rate measurements remain separate; `evals/trigger-evals.json` labels the previous measurement historical until the revised description is rerun through a host's implicit-invocation path.

The current unreleased v1.7 lifecycle evidence under `evals/results/v1.7.0-lifecycle-forward-test/` is likewise a single clean-source snapshot: five framework and cross-framework cases, 25/25 human-graded assertions, schema-v3 runner and grading provenance, and a summary that the harness recomputes from the complete trial set.

---

## Repository layout

```
tui-design-skill/
├── AGENTS.md                      # repository and release-note conventions
├── .claude-plugin/
│   └── marketplace.json          # plugin marketplace catalog
├── .github/
│   └── workflows/
│       ├── release.yml           # validates + attaches the tagged .skill release asset
│       └── validate.yml          # validates pull requests and main
├── scripts/
│   ├── eval_harness.py           # records, scores, and validates model eval runs
│   ├── package-skill.sh          # deterministically builds dist/tui-design.skill
│   └── validate-release.sh       # checks metadata, content, eval JSON, and package output
├── tests/
│   ├── test_eval_harness.py      # runner/scoring/integrity integration tests
│   └── test_packaging.py         # exact package-contract regression tests
├── plugins/
│   └── tui-design/
│       ├── .claude-plugin/
│       │   └── plugin.json       # plugin manifest
│       └── skills/
│           └── tui-design/
│               ├── SKILL.md      # slim routing + cross-cutting core (139 lines)
│               ├── agents/
│               │   └── openai.yaml # Codex UI and invocation metadata
│               └── references/
│                   ├── ecosystem-go.md
│                   ├── ecosystem-rust.md
│                   ├── ecosystem-python.md
│                   ├── ecosystem-typescript.md
│                   ├── cli-basics.md
│                   ├── visual-patterns.md
│                   ├── interaction-patterns.md
│                   └── exemplar-apps.md
├── evals/                        # versioned prompt/assertion sets and curated results
│   ├── README.md                 # evidence, privacy, and schema contract
│   ├── schema/v3/                # run, grade, and summary JSON Schemas
│   ├── evals.json
│   ├── build-evals.json
│   ├── tier2-content-evals.json
│   ├── tier3-content-evals.json
│   ├── v151-correction-evals.json
│   ├── v160-structural-evals.json
│   ├── v161-correction-evals.json
│   ├── v170-lifecycle-evals.json
│   ├── trigger-evals.json
│   └── results/                  # reviewed, committed run evidence
├── CHANGELOG.md
├── README.md
├── LICENSE
└── .gitignore
```

The nesting (`plugins/tui-design/skills/tui-design/`) is the Claude Code plugin format used by the marketplace. The optional `agents/openai.yaml` follows OpenAI's skill metadata format so Codex can present and invoke the same skill cleanly.

---

## License

[MIT](./LICENSE) — use it, fork it, ship it.

## Contributing

Issues and pull requests welcome. Particularly useful contributions:

- **Fixes to ecosystem references** when libraries change (a new Bubble Tea or Lipgloss major, Ratatui adds new widgets, Textual ships new APIs)
- **New exemplar apps** worth studying with concrete lessons
- **Clarifications** where the skill's advice produced unexpected results in real use
- **Translations** of the skill into other languages

When opening a PR that changes skill behavior, follow the [`evals/README.md`](evals/README.md) evidence contract and include the eval set, exact provider/model/runner metadata, exposed generation settings, repetitions, grading provenance, and validated summary. Do not claim an improvement from prompts and assertions alone.

## Acknowledgements

The principles in this skill draw on the public design wisdom of the Charm team (Bubble Tea, Lipgloss), the Ratatui maintainers, the Textual team at Textualize, the Ink maintainers, the [`clig.dev`](https://clig.dev) authors, and the many TUI authors whose apps are studied as exemplars within. The synthesis is mine; the design tradition is theirs.
