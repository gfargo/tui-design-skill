**For a new project, I’d choose Bubble Tea + Lipgloss, with Bubbles for lists, inputs, and scrolling.** Multiple panels alone aren’t a reason to choose gocui.

Lazygit’s feel comes from its interaction design: stable pane positions, numeric pane jumps, context-sensitive actions, and visible keyboard hints. Those transfer well to Bubble Tea.

| Library | Choose it when… | Main tradeoff |
|---|---|---|
| **Bubble Tea + Lipgloss** | You want custom panes and explicit, testable state transitions | You implement layout and focus routing |
| **tview** | Tables, trees, and forms dominate the interface | Retained widgets and callbacks shape your architecture |
| **gocui** | You specifically prefer named rectangular views whose buffers implement `io.Writer`, or maintain an existing app | More application structure is your responsibility |

There’s also a dependency distinction: lazygit copied its gocui fork into its own repository as `pkg/gocui` in April 2026. Choosing an external gocui package doesn’t give you exactly lazygit’s implementation.

For Bubble Tea, use a root model that owns layout, focus, and shared data; child models own each pane’s selection and scroll position. Route keyboard input to the focused child, and run disk, network, and subprocess work through asynchronous commands.

Treat this as a full-screen alternate-screen session. A simple responsive plan:

```text
Wide                              60 columns
┌─ Resources ──┬─ Details ──────┐  Resources | Details
│ > selected  │ selected item │  > selected
│   item      │               │    item
└─────────────┴───────────────┘
Tab focus  / filter  ? help       Enter details  / filter  ? help
```

At **80×24**, keep a compact list/detail split and hide secondary panes. At **60 columns**, show one pane with drill-down and back navigation, preserving selection. Declare a hard minimum—for example, 40×10—below which you show a truthful “terminal too small” message.

Keep border nesting to one level, omit an outer decorative frame, and use one selection marker rather than repeated row icons. Show loading, empty, and error states inside the affected pane.

**Choose gocui if its views-as-buffers model is what you want to program against. Choose Bubble Tea if the goal is a new app with lazygit’s workflow.**