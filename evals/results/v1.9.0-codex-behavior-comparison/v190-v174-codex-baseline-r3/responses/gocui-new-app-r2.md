**I’d default to Bubble Tea for a new Go TUI**, even one with lazygit-style panels. Choose gocui if you specifically prefer its imperative model: positioned views, direct updates, and keybindings attached to views.

The main tradeoff is how you manage application state:

| | gocui | Bubble Tea |
|---|---|---|
| Mental model | Views, coordinates, callbacks | State, messages, updates, rendering |
| Multi-panel layout | Direct control over rectangular views | Compose panel models and render them together |
| Background work | Coordinate goroutines and UI updates | Commands return messages into the update loop |
| Best fit | You want explicit control of views | You expect substantial state and asynchronous behavior |

Lazygit proves gocui can support a sophisticated interface. It doesn’t establish that it’s the best starting point today: much of lazygit’s behavior comes from its own architecture above the library.

For a Git-like app with background commands, selection changes, modal dialogs, and panels that update each other, **Bubble Tea’s explicit state flow is a useful advantage**. Keep shared state and focus in a root model; let each panel own its local selection and scrolling state. Use Lip Gloss for layout and styling.

If you want to position views and mutate them directly—and that feels simpler to you—gocui is a reasonable choice. Just expect to build more of the coordination structure yourself.