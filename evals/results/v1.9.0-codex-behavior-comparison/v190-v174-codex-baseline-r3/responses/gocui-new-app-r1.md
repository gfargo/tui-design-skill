**I’d default to Bubble Tea for a new Go TUI**, even if the layout looks like lazygit. Choose gocui when its low-level approach specifically appeals to you.

The key difference is how you manage application state:

| Library | Best fit | Main tradeoff |
|---|---|---|
| **Bubble Tea** | Custom interfaces with multiple panels, background commands, and explicit state transitions | You implement layout and focus management yourself |
| **gocui** | Rectangular views, direct drawing, and keybindings attached to views | More manual coordination as state and interactions grow |
| **tview** | Fast assembly from widgets such as tables, trees, forms, and flex layouts | Highly custom interactions can require working around widget conventions |

Lazygit shows that gocui can support a sophisticated interface. It also has substantial application-specific machinery for layout, focus, popups, and navigation; choosing the same library doesn’t give you that machinery.

For your app, I’d use **Bubble Tea with a root model that owns layout, focus, and global shortcuts**, plus a model per panel. Route keyboard input to the focused panel, and let background results update whichever panel owns that data. Use Lip Gloss for styling.

**Pick gocui instead if you prefer thinking in views and callbacks**, and want direct control over drawing. That’s a valid choice—just make it for the programming model, rather than because lazygit uses it.