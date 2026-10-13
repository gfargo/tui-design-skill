The three tools don't all share one default. fzf and fd use smart-case out of the box. ripgrep is case-sensitive unless you ask for smart-case.

| Tool | Default | Flags to change it |
|---|---|---|
| **fzf** | Smart-case | `-i` always ignores case, `+i` always matches case |
| **fd** | Smart-case | `-i` / `--ignore-case`, `-s` / `--case-sensitive` |
| **ripgrep (`rg`)** | Case-sensitive | `-S` / `--smart-case` turns on smart-case, `-i` ignores case. Many people put `--smart-case` in their `RIPGREP_CONFIG_PATH` file so it's always on. |

**How smart-case works:** if the query is all lowercase, matching ignores case. If it has any uppercase letter, matching respects case. So `readme` matches `README.md`, but `README` won't match `readme.txt`.

**For your filter box:** use smart-case by default. That matches fzf and fd, the two tools closest to an interactive filter. It also matches what most people have set up for rg anyway. Some tips:

- **Check the raw query for uppercase.** Decide on case before any normalization, and check the whole query, not each word. In Unicode, test whether each character is uppercase, not just A–Z.
- **Add an override if your users need one.** For example, a key that cycles smart → ignore → match case. Show the current mode in the prompt or status line, like fzf's `+i`.
- **Highlight the match correctly.** When matching ignores case, highlight the original text, not the lowercased copy.

The skill's filter guidance is in `references/interaction-patterns.md` under *Search and filter*: sub-100ms updates, a match count, highlighting and smart-case.
