Their defaults differ:

| Tool | Default case handling |
|---|---|
| **fzf** | **Smart case**: case-insensitive unless the query contains an uppercase letter. |
| **fd** | **Smart case**: case-insensitive unless the pattern contains an uppercase letter. |
| **ripgrep (`rg`)** | **Case-sensitive**. Smart case requires `-S` / `--smart-case`; case-insensitive matching requires `-i`. |

For your filter box, **smart case** matches fzf and fd: `foo` matches both `foo` and `Foo`, while `Foo` matches only that capitalization. It also matches ripgrep when users enable `--smart-case`.