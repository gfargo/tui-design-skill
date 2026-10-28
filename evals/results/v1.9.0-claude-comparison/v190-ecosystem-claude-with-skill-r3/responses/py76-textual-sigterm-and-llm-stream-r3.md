Both problems have direct fixes in Textual 8.

## 1. Streaming: use `Markdown.get_stream()` and `anchor()`

Every `markdown.update(full_text)` call parses and lays out the whole reply again, so each token costs more than the one before. `Markdown.get_stream()` appends only the new fragment. When tokens arrive faster than the widget can render (about 20 appends a second), it combines the queued fragments into one update. To make the view follow the text, call `anchor()` on the scroll container. It keeps the view pinned to the bottom until the user scrolls up, so they can still read earlier parts of the reply without being pulled back down.

```python
from textual import work
from textual.containers import VerticalScroll
from textual.widgets import Markdown

@work(exclusive=True)
async def stream_reply(self, chunks) -> None:
    self.query_one("#chat", VerticalScroll).anchor()
    markdown = self.query_one("#reply", Markdown)
    stream = Markdown.get_stream(markdown)
    try:
        async for chunk in chunks:      # pass each token, not the accumulated text
            await stream.write(chunk)
    finally:
        await stream.stop()             # sends any queued text, even on cancel or error
```

Things to watch for:
- **Pass the new fragment to `stream.write()`, not `full_text`.** If you keep building a `full_text` string for history or saving, store it separately and don't send it to the widget.
- **Call `stream.stop()` in `finally`.** Without it, the last batched fragment can be lost when the worker ends or is cancelled.
- **Run this as a worker** (`@work`), not in an event handler. That keeps the UI responsive while the reply streams. `exclusive=True` cancels the previous reply's stream if the user sends a new message mid-stream.
- `anchor()` needs to be called on the scrolling container (`VerticalScroll` or similar) that holds the messages, not on the `Markdown` widget itself.

## 2. SIGTERM: let Textual's event loop handle shutdown

Textual handles Ctrl+Q and its other quit paths, but it installs **no SIGTERM handler**. By default, `kill <pid>` ends the Python process immediately. Textual's shutdown code never runs, so the terminal stays in raw mode with the alternate screen and mouse tracking still on.

The fix is to have the asyncio loop catch SIGTERM and call `self.exit()`. That runs the normal shutdown path, and Textual restores the terminal itself:

```python
import asyncio
import signal
import sys
from textual.app import App

class ChatApp(App):
    def on_mount(self) -> None:
        if sys.platform != "win32":  # add_signal_handler raises NotImplementedError on Windows
            asyncio.get_running_loop().add_signal_handler(
                signal.SIGTERM, lambda: self.exit(return_code=143))

if __name__ == "__main__":
    app = ChatApp()
    app.run()
    sys.exit(app.return_code or 0)
```

Notes:
- **Don't use `signal.signal()` and don't write terminal reset codes yourself.** That handler can interrupt the program at any point, including halfway through drawing the screen. `loop.add_signal_handler` waits and runs the callback on the event loop between tasks, so the shutdown is clean.
- **Exit code 143** is the convention for SIGTERM (128 + 15), so supervisors and scripts can see why the app stopped. `return_code` only takes effect if you pass it to `sys.exit()` after `run()`, as shown above.
- **`kill -9` (SIGKILL) can't be caught,** so nothing can clean up after it. If that happens, run `reset` in the terminal.
- Your streaming worker gets cancelled during shutdown, and its `finally: await stream.stop()` still runs. The two fixes work together.

To check the fix: start the app, run `kill <pid>` from another terminal, and confirm your shell prompt comes back with normal echo, cursor and scrollback. `echo $?` should print `143`.
