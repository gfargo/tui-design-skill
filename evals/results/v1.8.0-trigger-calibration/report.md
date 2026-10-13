# Trigger calibration (v1.8.0 description)

This study measures whether the skill activates on its own, through each host's normal install path, when a prompt does or doesn't call for it. The prompts never name the skill. It covers Claude Code and Codex separately; the hosts load skills differently, so read each column on its own.

## Protocol

- **Description:** the `SKILL.md` description released in v1.8.0, unchanged since. Both manifests record its SHA-256 (`65f36b1b…`) and text. The skill tree (`47f010b6…`) is `main` after #64, which added one sentence to `visual-patterns.md` and left the description alone.
- **Prompts:** [`evals/v180-trigger-evals.json`](../../v180-trigger-evals.json) (SHA-256 `ef56e0d2…`): 19 positive, 15 adjacent, 5 ambiguous, and 3 unrelated prompts. P01–P12 and N01–N12 repeat the historical 2026-07-10 set.
- **Claude Code 2.1.295, `claude-opus-5-5`:** `claude -p` from an empty directory with `--plugin-dir plugins/tui-design` and `--setting-sources project`. The plugin skill `tui-design:tui-design` competes only with Claude Code's bundled skills; the user's installed plugins and skill copies stay off. A trial counts as triggered when the model calls the Skill tool for `tui-design:tui-design` within three turns.
- **Codex CLI 0.160.0, `gpt-6.1-sol` at low reasoning effort:** `codex exec` from an empty subdirectory of a scratch git repository whose `.agents/skills/tui-design` holds a copy of the skill, the same discovery path `npx skills add` uses at user scope. Every user-installed skill is disabled through `skills.config`, web search is off, and the sandbox is read-only. A trial counts as triggered when a command reads `tui-design/SKILL.md`; listing the directory doesn't count.
- **Design:** three repetitions per prompt and host, 126 trials per host, all valid. Both runs started from clean commit `5773b62`.
- **Runner:** [`scripts/runners/trigger_probe.py`](../../../scripts/runners/trigger_probe.py). Each host's `results.jsonl` keeps every trial's outcome and the first ten tool calls behind it.

## Results

| Category | Expected | Claude Code | Codex |
|---|---|---:|---:|
| Positive (19 prompts) | trigger | 57/57 | 57/57 |
| Adjacent (15 prompts) | don't trigger | 0/45 | 1/45 |
| Unrelated (3 prompts) | don't trigger | 0/9 | 0/9 |
| Ambiguous (5 prompts) | no expectation | 6/15 | 14/15 |

Every positive prompt triggered on both hosts in every repetition, including the weak-anchor prompts that never say "TUI" or name a framework: a terminal app's CI snapshots (P02), a file picker that should `cd` the shell (P06), a CLI table that people pipe into `grep` (P13), and a "yazi for S3" request (P17).

The only adjacent trigger was Codex reading the skill once in three runs for a neovim color scheme (N14), a case the description already excludes as editor configuration. The historical set's three misses no longer occur on either host: the VS Code Nerd Font question (N08), React profiling (N02), and Next.js API keys (N05) were 0/3 everywhere.

The hosts disagree on the ambiguous prompts. Both loaded the skill for a CI progress bar that floods logs (A01) and a CLI startup banner (A05). Codex also loaded it for a tmux status bar, a zsh prompt theme, and colored service logs (A02–A04), which Claude never did. Codex's trigger is cheaper (reading one file, not invoking a tool), and it loaded the skill whenever a prompt involved terminal output.

| ID | Category | Prompt area | Claude | Codex |
|---|---|---|---:|---:|
| P01 | positive | testing, framework anchor | 3/3 | 3/3 |
| P02 | positive | testing, weak anchor (only 'terminal app') | 3/3 | 3/3 |
| P03 | positive | debugging, framework anchor | 3/3 | 3/3 |
| P04 | positive | profiling, framework anchor | 3/3 | 3/3 |
| P05 | positive | OSC 52 over ssh and tmux, weak anchor | 3/3 | 3/3 |
| P06 | positive | shell integration, weak anchor | 3/3 | 3/3 |
| P07 | positive | inline vs alternate screen, named apps | 3/3 | 3/3 |
| P08 | positive | CLI first run and auth | 3/3 | 3/3 |
| P09 | positive | forms, weak anchor | 3/3 | 3/3 |
| P10 | positive | Nerd Font fallback | 3/3 | 3/3 |
| P11 | positive | build, named app | 3/3 | 3/3 |
| P12 | positive | framework choice | 3/3 | 3/3 |
| P13 | positive | CLI output contract, weak anchor | 3/3 | 3/3 |
| P14 | positive | accessibility, framework anchor | 3/3 | 3/3 |
| P15 | positive | terminal modes, framework anchor | 3/3 | 3/3 |
| P16 | positive | East Asian width, weak anchor | 3/3 | 3/3 |
| P17 | positive | named app without 'TUI' | 3/3 | 3/3 |
| P18 | positive | interactive prompts | 3/3 | 3/3 |
| P19 | positive | CLI help text | 3/3 | 3/3 |
| N01 | adjacent | web testing | 0/3 | 0/3 |
| N02 | adjacent | web profiling | 0/3 | 0/3 |
| N03 | adjacent | browser clipboard | 0/3 | 0/3 |
| N04 | adjacent | shell script with no interface | 0/3 | 0/3 |
| N05 | adjacent | web secrets | 0/3 | 0/3 |
| N06 | adjacent | web forms | 0/3 | 0/3 |
| N07 | adjacent | ssh connectivity | 0/3 | 0/3 |
| N08 | adjacent | editor font | 0/3 | 0/3 |
| N09 | adjacent | backend profiling | 0/3 | 0/3 |
| N10 | adjacent | desktop GUI | 0/3 | 0/3 |
| N11 | adjacent | shell one-liner | 0/3 | 0/3 |
| N12 | adjacent | web layout | 0/3 | 0/3 |
| N13 | adjacent | terminal emulator font configuration | 0/3 | 0/3 |
| N14 | adjacent | editor configuration | 0/3 | 1/3 |
| N15 | adjacent | CI scripting with no interface | 0/3 | 0/3 |
| A01 | ambiguous | progress output in CI logs | 3/3 | 2/3 |
| A02 | ambiguous | tmux status line configuration | 0/3 | 3/3 |
| A03 | ambiguous | shell prompt theme | 0/3 | 3/3 |
| A04 | ambiguous | service log formatting | 0/3 | 3/3 |
| A05 | ambiguous | startup banner | 3/3 | 3/3 |
| C01 | negative | SQL | 0/3 | 0/3 |
| C02 | negative | Kubernetes | 0/3 | 0/3 |
| C03 | negative | networking concepts | 0/3 | 0/3 |

## Decision

The description stays as it is. On both hosts it activated for every prompt it should cover and stayed off for 89 of 90 adjacent trials. Narrowing it to exclude terminal configuration such as tmux or shell prompts would target prompts that only Codex picks up, and only as a cheap read; it would also risk missing real requests, which costs more than an extra read.

## Limitations

- **One install path per host:** Claude used a `--plugin-dir` plugin and Codex a project-scoped skill. A marketplace install or a user-scoped `~/.agents/skills` copy uses the same name and description, but other installed skills on a real machine compete for the same prompts.
- **Turn limit:** a Claude trial stops after three turns, so a model that would load the skill later in a long session counts as not triggered.
- **Small ambiguous set:** five ambiguous prompts show where the hosts differ, not a rate to generalize.
