**80 columns** (80 characters):
```text
Enter open  / filter  j/k move  r refresh  d delete  y copy path  ? help  q quit
```

**40 columns** (38 columns; `↵` means Enter):
```text
↵ open / filter j/k move ? help q quit
```

At 40, drop `r refresh`, `d delete`, and `y copy path`: they’re less frequent than open, filter, and movement. Keep help for discovering omitted actions and quit for an obvious exit.

Edit, sort, tag, and command are omitted at both widths because they’re used least; keep them discoverable through `? help`.