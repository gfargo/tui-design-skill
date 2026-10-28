**For a new project, I’d use Bubble Tea + Lipgloss, adding Bubbles components where useful.** Lazygit’s multi-panel interaction works well with that stack.

There’s also a wrinkle in the premise: lazygit now maintains its gocui fork **inside its own repository** (`pkg/gocui`, since April 2026). Choosing a standalone gocui package doesn’t give you the exact framework lazygit uses.

| Choice | When it fits |
|---|---|
| **Bubble Tea + Lipgloss** | Custom panes, complex state, asynchronous operations, and independently testable updates. You own layout and focus routing. |
| **tview** | You want ready-made tables, trees, forms, and layout containers with a callback-based API. |
| **gocui** | You specifically prefer named rectangular views with writable text buffers and per-view keybindings, or you’re maintaining an existing app. |

For Bubble Tea, put focus, pane selection, dimensions, and overlays in a root model. Route keyboard input to the focused pane; run I/O through commands that return messages. Compose pane output with Lipgloss.

Borrow lazygit’s **stable pane positions, numeric pane shortcuts, context actions, and contextual help**. Plan the narrow layout early:

```text
Wide                           60-column split
+------------+---------------+ +---------------------------+
| 1 Items    | Detail        | | Items | Detail             |
|            |               | | Active pane fills width   |
+------------+               | |                           |
| 2 History  |               | | Enter: detail; Esc: back   |
+------------+---------------+ +---------------------------+
| contextual shortcuts       | | contextual shortcuts      |
+----------------------------+ +---------------------------+
```

At 80×24, keep a compact sidebar and detail pane; at 60 columns, switch to one pane while preserving selection. Below your measured minimum, show a resize message and keep quit working. Avoid an outer border around already bordered panes, repeated row markers, and duplicate status labels.

**Choose gocui for its programming model—not because you want lazygit’s appearance.**