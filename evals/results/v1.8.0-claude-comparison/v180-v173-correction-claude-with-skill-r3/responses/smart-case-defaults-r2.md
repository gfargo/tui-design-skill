They don't all behave the same way. fzf and fd use smart-case by default, but ripgrep is case-sensitive by default.

| Tool | Default | Flags to change it |
|---|---|---|
| **fzf** | Smart-case | `-i` always ignores case, `+i` always matches case |
| **fd** | Smart-case | `-i` / `--ignore-case`, `-s` / `--case-sensitive` |
| **ripgrep** | Case-sensitive | `-S` / `--smart-case`, `-i` / `--ignore-case`. Many people set `--smart-case` in `RIPGREP_CONFIG_PATH`. |

**Smart-case** means:
- If the query is all lowercase, case is ignored. `readme` matches `README.md`.
- If the query has any uppercase letter, case matters. `README` matches `README.md` but not `readme.txt`.

**For your filter box:** use smart-case as the default. It's what fzf and fd users expect. It's also what ripgrep users usually turn on, so it won't surprise anyone. The skill's guidance (`references/interaction-patterns.md:309`) says the same thing.

The logic is short:

```
case_sensitive = query != query.lower()
```

Some additions that make it easier to use:
- **Show the current mode** in or next to the filter box, for example a small `Aa` or `smart` label. Otherwise users can't tell why typing one capital letter dropped results.
- **Add an override key** if users may need to force a mode. fzf's `+i`/`-i` pattern works well: a toggle that cycles smart → ignore → sensitive.
- **Use the same rule in your highlighting**, so the highlighted characters are exactly what the matcher matched.

The skill also lists other filter-box rules in the same section: update results in under 100ms, show a match count, highlight matched characters, and clear the filter with `Esc`.
