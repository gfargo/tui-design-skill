Their defaults differ:

| Tool | Default case handling |
|---|---|
| **fzf** | **Smart case**: case-insensitive unless the query contains an uppercase letter. |
| **fd** | **Smart case**: case-insensitive unless the pattern contains an uppercase letter. |
| **ripgrep (`rg`)** | **Case-sensitive**, regardless of the pattern’s capitalization. Use `-S` / `--smart-case` for smart case. |

For your TUI, **smart case** matches fzf and fd: `foo` matches `foo`, `Foo`, and `FOO`; `Foo` matches only that capitalization.

All three support `-i` / `--ignore-case`. To force case-sensitive matching, fzf uses `+i`, while fd and rg use `-s` / `--case-sensitive`.