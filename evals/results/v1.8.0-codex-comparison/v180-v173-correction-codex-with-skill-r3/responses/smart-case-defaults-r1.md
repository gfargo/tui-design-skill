Use **smart-case** for your filter box to match fzf and fd. Ripgrep’s default differs.

| Tool | Default case handling | Overrides |
|---|---|---|
| **fzf** | Smart-case: lowercase query ignores case; any uppercase letter makes matching case-sensitive. | `-i` ignores case; `+i` forces case-sensitive matching. |
| **fd** | Smart-case, with the same rule. | `-i` / `--ignore-case`; `-s` / `--case-sensitive`. |
| **ripgrep (`rg`)** | Always case-sensitive by default. | `-i` / `--ignore-case`; `-S` / `--smart-case`. |

For a simple filter, `foo` should match `foo`, `Foo`, and `FOO`; `Foo` should require that capitalization. There’s no single policy matching all three defaults—smart-case matches **fzf, fd, and `rg -S`**.