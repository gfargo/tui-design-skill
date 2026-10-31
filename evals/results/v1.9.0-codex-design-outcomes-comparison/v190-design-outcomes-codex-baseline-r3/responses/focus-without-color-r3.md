Use an explicit `[FOCUSED]` label and `=` borders so focus remains visible without color.

Files focused:
```text
+=======================+ +--------------------------------------+
| Files [FOCUSED]       | | Preview                              |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+=======================+ +--------------------------------------+
```

Preview focused:
```text
+-----------------------+ +======================================+
| Files                 | | Preview [FOCUSED]                    |
| > main.go             | | package main                         |
|   util.go             | |                                      |
|   README.md           | | func main() {                        |
+-----------------------+ +======================================+
```

The `>` continues to mark the selected file; the label and border identify keyboard focus.