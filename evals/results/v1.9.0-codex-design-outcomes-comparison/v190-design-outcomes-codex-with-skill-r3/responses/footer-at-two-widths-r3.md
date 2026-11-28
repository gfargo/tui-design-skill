**80 columns** — 53 cells:
```text
Enter open | / filter | j/k move | r refresh | ? help
```

**40 columns** — 30 cells:
```text
Enter open | / filter | ? help
```

At 40, drop `r refresh` (20%) first, then `j/k move` (35%). Keeping move would require 41 cells. Preserve `? help` last so every omitted action remains discoverable.

At 80, keep the four most frequent actions plus help; spare width needn’t become clutter. Delete, copy path, edit, sort, tag, command, and quit stay in help. Both lines use ASCII separators, with no borders or decorative markers.