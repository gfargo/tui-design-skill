No. **Both normally reach a Bubble Tea app running in raw mode.** The claim confuses terminal input modes:

| Key | Cooked mode, with usual settings | Bubble Tea’s raw mode |
|---|---|---|
| Ctrl+S | TTY driver pauses output through XOFF flow control | Delivered as a keypress; flow control is disabled |
| Ctrl+C | TTY driver generates SIGINT | Delivered as a keypress; your app decides what happens |

**Use Ctrl+S for save.** You normally don’t need users to run `stty -ixon`. Raw mode controls this behavior; the alternate screen itself doesn’t.

**Ctrl+C for copy is technically possible, but I recommend keeping it for cancel/quit.** Use `y` for copy outside text entry, or another discoverable binding. If you deliberately repurpose Ctrl+C, provide an obvious cancel/quit route.

Handle `"ctrl+s"` and `"ctrl+c"` in `Update`: Bubble Tea v2 uses `tea.KeyPressMsg`; v1 uses `tea.KeyMsg`. Copying to the system clipboard also requires a clipboard operation—receiving the shortcut doesn’t do that automatically.

Terminal emulator shortcuts or multiplexer bindings can still intercept keys before Bubble Tea sees them. For example, Zellij’s default bindings capture Ctrl+S, so offer another save route in help or a command menu.