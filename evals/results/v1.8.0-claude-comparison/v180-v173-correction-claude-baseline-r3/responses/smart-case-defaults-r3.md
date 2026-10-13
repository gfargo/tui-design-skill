Two of the three use **smart case** by default. ripgrep doesn't.

| Tool | Default | Flags |
|---|---|---|
| **fzf** | Smart case | `-i` forces case-insensitive, `+i` forces case-sensitive (newer versions also have `--ignore-case`, `--no-ignore-case`, `--smart-case`) |
| **fd** | Smart case | `-s`/`--case-sensitive`, `-i`/`--ignore-case` |
| **ripgrep** | **Case-sensitive** | `-S`/`--smart-case`, `-i`/`--ignore-case`, `-s`/`--case-sensitive` |

**Smart case** means the search ignores case if the query is all lowercase and becomes case-sensitive once it contains an uppercase letter. For example, `foo` matches `Foo`, but `Foo` doesn't match `foo`.

A few details that matter if you want to copy the behavior exactly:

- **ripgrep's default is often overridden.** Many people put `--smart-case` in their `RIPGREP_CONFIG_PATH` config. That's probably why it feels like all three behave the same.
- **Only literal uppercase counts.** In fd and ripgrep, regex escapes like `\S` or `\W` don't switch on case sensitivity. If your filter is plain text, this doesn't affect you.
- **Scope of the check:**
  - fzf checks the whole query at once, so one capital letter anywhere makes all search terms case-sensitive.
  - ripgrep checks each pattern separately when you pass several with `-e`.
- **The last flag wins.** In both fd and ripgrep, if you pass several case flags, the last one takes effect. This is how a command-line flag can override a config file.

**My recommendation for your filter box:**
1. Make smart case the default, deciding from the whole query the way fzf does. Users of fzf and fd will expect this.
2. Add a toggle that cycles between smart, ignore, and respect case, and show the current mode in the UI. fzf doesn't show its mode, which is a common source of confusion.
3. To check for uppercase, test whether `query != query.lower()` using Unicode-aware lowercasing, not just a check for ASCII A–Z.
4. Compare text with case folding (e.g. `casefold()` in Python) rather than `lower()`, so cases like `ß`/`SS` work correctly.

I answered this from memory and didn't check it against current docs. Flag names can change between versions, so running `fzf --help`, `fd --help` and `rg --help` will confirm them for the versions you have installed.
