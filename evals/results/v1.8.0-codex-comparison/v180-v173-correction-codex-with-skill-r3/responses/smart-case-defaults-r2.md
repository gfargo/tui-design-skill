Use **smart-case** for your filter box to match fzf and fd. The three tools differ:

| Tool | Default case handling |
|---|---|
| **fzf** | Smart-case: lowercase queries ignore case; any uppercase letter makes matching case-sensitive. |
| **fd** | Smart-case, with the same rule. |
| **ripgrep (`rg`)** | Case-sensitive. Smart-case requires `-S` / `--smart-case`; `-i` always ignores case. |

For a smart-case filter, `foo` matches both `foo` and `Foo`, while `Foo` matches only that casing. All-uppercase queries such as `FOO` are also case-sensitive.

These are built-in defaults; user flags or configuration can override them.