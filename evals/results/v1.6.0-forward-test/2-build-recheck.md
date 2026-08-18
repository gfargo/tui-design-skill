No—this is a summon–choose–exit tool, so use a bounded inline Bubble Tea picker, not a full-screen app.

Output contract:

- On selection: write exactly `branch-name\n` to stdout and exit `0`.
- Put prompts, filtering UI, diagnostics, and a final `selected: branch-name` line on `/dev/tty` or stderr.
- On `Esc`: write nothing to stdout and exit nonzero.
- On `Ctrl+C`: restore the terminal, write nothing to stdout, and exit `130`.
- Never emit ANSI codes or logs on stdout.

For safer cancellation and quoting, recommend:

```sh
branch=$(branchpick) && git checkout "$branch"
```

The literal `git checkout $(branchpick)` works after a selection, but cancellation still runs `git checkout` with no branch. The assignment form preserves `branchpick`’s exit status.

Run Bubble Tea against the controlling terminal with `tea.WithInput(tty)` and `tea.WithOutput(tty)`, while reserving process stdout for the result. Leave `tea.View.AltScreen` false and mouse capture off. After Bubble Tea restores cooked mode, print the permanent `selected:` summary to the terminal. That preserves the typed shell command and chosen branch in scrollback.

Important implementation choices:

- Define “recent” explicitly. Prefer checkout recency from the `HEAD` reflog, deduplicate targets, verify they remain local branches, then append other local branches ordered by committer date.
- Invoke Git with `exec.CommandContext`; never construct a shell command.
- Load branches before entering raw mode, or use a Bubble Tea command if loading asynchronously.
- Keep the original refname separate from highlighted display text.
- Use a fuzzy matcher with recency as a stable tie-breaker.
- Since typing always edits the filter, use arrows for navigation; `j`, `k`, and `q` must remain searchable characters. Show `↑↓ move · enter select · esc cancel`.
- Bound the picker to roughly 8–10 results. At 60 columns, hide metadata and truncate by terminal-cell width; at very small sizes, show only the query and current match.
- If no controlling TTY exists, fail clearly without producing stdout. An optional `--list` mode can provide plain, one-branch-per-line automation output.

Test the pure pieces first: reflog parsing, deduplication, ordering, fuzzy ranking, filtering, cursor movement, and exact stdout bytes. Add pinned render goldens for 80×24, 60 columns, and the minimum layout with an ASCII/no-color profile. Finally, use one or two PTY tests to verify selection, cancellation, and interruption restore terminal settings, emit no alternate-screen sequences, keep UI off stdout, and leave the final chosen-branch line in scrollback.
