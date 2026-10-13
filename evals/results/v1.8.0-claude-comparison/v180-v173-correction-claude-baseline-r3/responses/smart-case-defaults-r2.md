They don't all have the same default.

| Tool | Default | Flags to override |
|---|---|---|
| **fzf** | **Smart case**: matching ignores case unless the query has an uppercase letter | `-i` always ignores case, `+i` always matches case, `--smart-case` is the default |
| **fd** | **Smart case**: same rule as fzf | `-i` / `--ignore-case`, `-s` / `--case-sensitive` |
| **ripgrep** | **Case-sensitive** | `-S` / `--smart-case`, `-i` / `--ignore-case`, `-s` / `--case-sensitive` |

ripgrep is the exception. Smart case is opt-in there, though many people turn it on in their `RIPGREP_CONFIG_PATH` config file. So smart case feels like the default to many users even though it isn't.

**Recommendation for a filter box: use smart case.** Two of the three tools do it by default, and it's what most users expect from interactive filtering.

Details worth copying:

- **Only uppercase letters typed by the user should count.** ripgrep and fd ignore uppercase in regex escapes like `\S` or `\W` when deciding. If your filter is plain text, just check whether the query differs from its lowercased form.
- **fzf decides per search term.** In fzf's default extended-search mode, each space-separated term chooses case on its own. So `foo Bar` matches `foo` without case and `Bar` with case. If your filter splits on spaces, do the same.
- **Use Unicode-aware lowercasing**, not ASCII-only, so queries like `É` behave correctly.
- **Optional extra:** fzf also ignores accents on Latin letters by default, so `cafe` matches `café`. `--literal` turns this off. It's a nice touch for a filter box, but it isn't really part of case handling.

A minimal version:

```
caseSensitive = query != lowercase(query)
match = caseSensitive ? contains(item, query)
                      : contains(lowercase(item), lowercase(query))
```

If you want users to be able to override it, add a toggle that cycles smart → ignore → respect. That mirrors fzf's `-i` / `+i`.
