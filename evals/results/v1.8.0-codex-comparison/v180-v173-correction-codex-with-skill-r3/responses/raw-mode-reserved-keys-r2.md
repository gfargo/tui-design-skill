No. **Both keys normally reach a Bubble Tea app**, because Bubble Tea puts the terminal into raw mode.

The advice confuses raw mode with the terminal’s usual cooked mode:

| Key | Cooked mode, typically | Bubble Tea raw mode |
|---|---|---|
| Ctrl+S | Stops output via XON/XOFF flow control, if enabled | Arrives as `"ctrl+s"` |
| Ctrl+C | Generates SIGINT | Arrives as `"ctrl+c"` for your app to handle |

**Use Ctrl+S for save.** You generally don’t need users to run `stty -ixon`; raw mode disables that flow control. The alternate screen itself isn’t what enables this—raw mode is.

**Ctrl+C for copy is technically possible, but I recommend preserving it for cancel/quit.** Use a discoverable copy binding such as `y` outside text entry, plus a menu or command-palette action. If you choose Ctrl+C for copy, provide an obvious cancel/quit route. Receiving the key and writing to the system clipboard are separate operations.

Terminal shortcuts or multiplexers can still intercept keys before they reach your app—for example, Zellij can capture Ctrl+S. Provide an alternative way to invoke save and copy.