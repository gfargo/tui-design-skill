They don't all do the same thing. Two default to smart-case and one doesn't:

| Tool | Default | Flags to change it |
|---|---|---|
| **fzf** | **Smart-case** | `-i` always ignores case, `+i` always matches case |
| **fd** | **Smart-case** | `-i` / `--ignore-case`, `-s` / `--case-sensitive` |
| **ripgrep** | **Case-sensitive** | `-S` / `--smart-case` turns on smart-case, `-i` ignores case |

**Smart-case** works like this: if the query is all lowercase, case is ignored. If it has any uppercase letter, matching becomes case-sensitive.

- `readme` matches `README.md`, `Readme.txt` and `readme`
- `README` matches only `README.md`

ripgrep is case-sensitive by default because it's a grep replacement and keeps grep's behaviour. Many users turn on smart-case permanently by putting `--smart-case` in the file that `RIPGREP_CONFIG_PATH` points to.

**What to do in your filter box:** a filter box works like fzf, so use smart-case by default. Typing lowercase finds everything, and adding a capital letter narrows the results. That's what people expect from fzf, fd and most editor pickers.

Some implementation details:
- **Only count real letters when checking for uppercase.** ripgrep ignores things like regex escapes (`\W`, `\S`) when deciding whether a pattern contains uppercase. If you support regex or other special syntax, skip those tokens in the check.
- **Use Unicode-aware lowercasing,** not ASCII-only. Your language's standard `toLowerCase` / `str.lower()` / `unicode.ToLower` is usually enough for a filter box.
- **Consider a way to switch modes** (smart, ignore case, match case) for advanced users. Show the current mode near the match count, e.g. `42/1300 [Aa]`, so users understand why a capitalised query returns fewer results.
- Keep the other basics from the skill's filter guidance (`references/interaction-patterns.md`, *Search and filter*): results update in under 100ms, a visible match count, highlighted matched characters, and `Esc` clears the filter.
