Their defaults differ:

| Tool | Default | Behavior |
|---|---|---|
| **fzf** | Smart case | Lowercase queries match either case; any uppercase letter makes the query case-sensitive. |
| **fd** | Smart case | Same: case-insensitive unless the pattern contains an uppercase letter. |
| **ripgrep (`rg`)** | Case-sensitive | Matches case exactly, even when the pattern is all lowercase. Use `--smart-case` (`-S`) to enable smart case. |

For your filter box, **smart case** follows fzf and fd: `foo` matches `foo`, `Foo`, and `FOO`; `Foo` matches only `Foo`.