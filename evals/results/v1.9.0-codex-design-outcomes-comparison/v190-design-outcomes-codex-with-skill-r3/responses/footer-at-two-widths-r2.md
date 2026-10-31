**80 columns** — 53 cells:
```text
Enter open | / filter | j/k move | r refresh | ? help
```

**40 columns** — 30 cells:
```text
Enter open | / filter | ? help
```

At 40, drop `r refresh` (20%), then `j/k move` (35%). Keeping movement alongside open, filter, and help would require 41 cells. Preserve the two most frequent actions and keep `? help` last so every omitted binding remains discoverable.

At 80, stop at five hints to keep the footer scannable. Delete, copy path, edit, sort, tag, command, and quit belong in help; spare width needn’t be filled.