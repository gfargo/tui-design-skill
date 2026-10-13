Two of the three use smart case by default. ripgrep doesn't.

| Tool | Default | Flags |
|---|---|---|
| **fzf** | Smart case | `-i` always ignores case, `+i` always respects it |
| **fd** | Smart case | `-i` / `--ignore-case`, `-s` / `--case-sensitive` |
| **ripgrep** | **Case-sensitive** | `-S` / `--smart-case` to opt in, `-i` to ignore case, `-s` to force case-sensitive |

**What "smart case" means:** if the query is all lowercase, the match ignores case. If it has any uppercase letter, the match is case-sensitive. So `foo` matches `Foo` and `FOO`, but `Foo` only matches `Foo`.

**ripgrep's default:** many people put `--smart-case` in their `~/.ripgreprc`, so it can feel like smart case is the default. It isn't.

**Details to copy if you want to match closely:**
- **fzf checks each term separately** (in its default extended-search mode). In `foo Bar`, `foo` ignores case while `Bar` is case-sensitive. A simple filter box usually treats the whole query as one unit. That's fine, but it differs from fzf for multi-word queries.
- **ripgrep and fd only count uppercase letters that are literal text** in the pattern. Escape sequences like `\S` or `\W` don't make the search case-sensitive. This only matters if your filter accepts regex.
- **Use Unicode-aware checks.** Decide "has uppercase" with a proper Unicode test (e.g., `ch.is_uppercase()`, or comparing `s.to_lowercase() != s`), not just ASCII A–Z. Then `É` also makes the match case-sensitive.

**Recommendation for a TUI filter box:** use smart case for the whole query, which is what fzf and fd do. Optionally add a toggle that cycles smart → ignore → respect, and show the current mode in the prompt. Users who know fzf will find it natural, and smart case rarely surprises anyone.
