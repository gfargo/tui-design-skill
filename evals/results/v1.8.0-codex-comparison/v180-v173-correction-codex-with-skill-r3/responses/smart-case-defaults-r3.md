Use **smart-case** for your filter box to match fzf and fd. The three tools don’t all share the same default:

| Tool | Default case handling |
|---|---|
| **fzf** | Smart-case: ignores case unless the query contains an uppercase letter. |
| **fd** | Smart-case: ignores case unless the pattern contains an uppercase letter. |
| **ripgrep (`rg`)** | Case-sensitive. Smart-case requires `-S` / `--smart-case`. |

With smart-case, `foo` matches `foo`, `Foo`, and `FOO`; `Foo` requires matching capitalization. All-uppercase queries are also case-sensitive.

For your TUI, default to smart-case and offer explicit “ignore case” and “match case” overrides. That follows the tui-design skill’s recommendation.