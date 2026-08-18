No. This is a summon–choose–exit picker, so use a bounded inline interface. Bubble Tea is reasonable for input handling and cleanup, but do not enable its alternate screen.

The output contract should be strict:

- Success: stdout contains exactly `branch-name\n`; exit `0`.
- Cancel (`Esc`/`Ctrl+C`): stdout is empty; exit `130`.
- Git, repository, or terminal error: stdout is empty; explanatory text goes to stderr; exit nonzero.
- Prompts, filtering results, ANSI sequences, and status messages never go to stdout.

Because command substitution captures stdout, connect Bubble Tea’s input/output to the controlling terminal (`/dev/tty` on Unix, with a platform abstraction for Windows). Use the normal screen buffer, temporary raw mode, no mouse capture, and no alternate screen. After Bubble Tea has restored the terminal, print a durable line such as `branchpick › feature/auth` to the terminal, then write only `feature/auth\n` to stdout. That leaves both the shell’s invoking command and the choice in scrollback.

Keep the UI small: query line, perhaps eight results, match count, and `↑/↓ select · enter choose · esc cancel`. Avoid borders and per-row decoration; one selection marker is enough. At 60 columns, truncate branch names by terminal cell width rather than wrapping.

One shell caveat: cancellation does not prevent the outer command in `git checkout $(branchpick)` from running. Recommend the safer form:

```sh
branch=$(branchpick) && git checkout -- "$branch"
```

Implementation choices:

- Enumerate local refs with `git for-each-ref`, without invoking a shell.
- Define “recent” explicitly. Sorting by branch-tip committer date is simple and deterministic; if “recently used” is intended, derive order from the HEAD reflog, deduplicate existing local branches, then append the remaining branches.
- Keep Git collection, fuzzy ranking, selection state, rendering, and process output separate.
- Use smart-case fuzzy matching and preserve a stable recency tie-breaker.
- Don’t bind printable navigation keys while the query field is active; use arrows, Enter, Esc, and Ctrl+C.
- Detect a missing controlling terminal and fail clearly rather than hanging.

The most valuable tests are:

- Unit tests for Git-output parsing, deduplication, recency ordering, fuzzy ranking, cursor movement, and empty/no-match states.
- Contract tests asserting that successful stdout is exactly one branch plus newline and that cancellation/errors emit no stdout.
- Temporary-repository integration tests with controlled branches and commit dates.
- Golden renders at 80×24 and 60 columns, including long and wide-character branch names, monochrome, and `NO_COLOR`.
- One PTY smoke test verifying selection, raw-mode restoration, absence of alternate-screen escape sequences, durable scrollback output, and clean Ctrl+C handling.
