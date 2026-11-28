Mark keyboard focus explicitly in the pane title so it remains visible without color.

Files focused:
```text
+-----------------------+ +--------------------------------------+
| Files [FOCUS]         | | Preview                              |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +--------------------------------------+
```

Preview focused:
```text
+-----------------------+ +--------------------------------------+
| Files                 | | Preview [FOCUS]                      |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +--------------------------------------+
```

The `>` still indicates the selected file; `[FOCUS]` identifies the pane receiving keyboard input.