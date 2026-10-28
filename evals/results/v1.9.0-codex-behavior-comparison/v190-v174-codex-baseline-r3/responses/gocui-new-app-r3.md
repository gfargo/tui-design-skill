**Gocui is a reasonable fit, but I wouldn’t choose it solely because lazygit uses it.** Lazygit’s polished behavior comes from substantial application code on top of the library.

Also, lazygit uses **[jesseduffield/gocui](https://github.com/jesseduffield/gocui)**, a fork of the original **jroimartin/gocui**. That distinction matters when evaluating features and maintenance.

For a new multi-panel Go TUI:

| Library | Best fit | Main tradeoff |
|---|---|---|
| **[gocui](https://github.com/jesseduffield/gocui)** | Explicit rectangular views, panel-specific keybindings, tight control | You build much of the widget behavior and state coordination |
| **[tview](https://github.com/rivo/tview)** | A dense interface with lists, trees, tables, forms, and split panes | Fast to assemble, but customization follows its widget model |
| **[Bubble Tea](https://github.com/charmbracelet/bubbletea)** | Custom interactions, asynchronous operations, and testable state transitions | You coordinate pane layout, focus, sizing, and message routing |

**For the app you described, I’d start with tview** if the panels mostly contain standard widgets. Choose Bubble Tea if custom interaction and background activity are central. Choose gocui if you specifically like its imperative view API and expect to implement your own UI components.

Whichever you choose, prototype the same small slice first: two panes, focus switching, independent scrolling, a popup, resizing, and one background operation. Those behaviors reveal the architectural fit much better than reproducing lazygit’s appearance.