Use **60–80% of the terminal width**, with a **30-column minimum** and an **approximately 80-column maximum** for prose. Center horizontally, slightly above vertical center. Measure in terminal cells.

Practical targets:

| Terminal width | Dialog width |
|---|---:|
| 120 columns | 72–80 columns |
| 80 columns | 48–64 columns |
| 60 columns | 36–48 columns |

Wrap the message as space shrinks; keep the consequence and controls visible. If they cannot fit, show a truthful “terminal too small” state.

With **`NO_COLOR` set to a non-empty value**, suppress automatic color and retain the modal’s structure:

- Clear the cells beneath the dialog before drawing it, preventing text bleed-through.
- Use one border, a descriptive title, and dialog-specific footer hints.
- Trap focus inside; `Esc` cancels and restores previous focus.
- Mark selection with text or shape, such as `> [Cancel]`.
- Treat background dimming as optional. Faint is an attribute, and some terminals ignore it; the modal must remain clear without it.

```text
Wide terminal                         60-column split
+----------------------------------+  +----------------------------------+
| Confirm deletion                 |  | Confirm deletion                 |
| Delete 3 files?                  |  | Delete 3 files?                  |
| This cannot be undone.           |  | This cannot be undone.           |
|                                  |  |                                  |
| > [Cancel]    [Delete]            |  | > [Cancel]    [Delete]            |
| Tab switch  Enter choose         |  | Tab switch  Enter choose         |
| Esc cancel                       |  | Esc cancel                       |
+----------------------------------+  +----------------------------------+
```

Short confirmations can stay compact across sizes. Default destructive confirmations to **Cancel/No**. Keep the chrome to one border and one focus marker; extra warning icons and nested boxes add little.