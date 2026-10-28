Use a fixed bottom bar with highlighted keys and quiet labels. At 40 columns, wrap into two rows and preserve action order.

**80 columns**
```text
F1 Help  F2 Rename  F3 View  F4 Edit  F5 Copy  F6 Move  F7 Mkdir  F8 Delete
```

**40 columns**
```text
F1 Help  F2 Rename  F3 View  F4 Edit
F5 Copy  F6 Move    F7 Mkdir F8 Delete
```

Render `F1`–`F8` in reverse video, with a subtle background across the full bar. Keep labels readable without color; disable unavailable actions by dimming their entire hint.