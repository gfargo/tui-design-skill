Use **Textual’s Markdown stream API**, anchor the scrolling container, and route SIGTERM through `App.exit()`.

Replace the per-token `markdown.update(full_text)` loop with this method in your app:

```python
from textual import work
from textual.containers import VerticalScroll
from textual.widgets import Markdown

@work(exclusive=True, group="reply")
async def stream_reply(self, chunks) -> None:
    # These IDs refer to your scroll container and reply Markdown.
    self.query_one("#chat-scroll", VerticalScroll).anchor()
    markdown = self.query_one("#reply", Markdown)

    stream = Markdown.get_stream(markdown)
    try:
        async for chunk in chunks:
            await stream.write(chunk)  # New text only, not full_text.
    finally:
        await stream.stop()  # Flush queued text.
```

`Markdown.get_stream()` batches incoming fragments when rendering falls behind, avoiding a full reply replacement for every token. `anchor()` follows the growing content until the user scrolls up, allowing them to read earlier messages. Run the LLM request with an async client so it doesn’t block the UI.

**Textual 8 does not install a SIGTERM handler.** On Unix, register one on the running event loop:

```python
import asyncio
import signal
import sys

from textual.app import App

class ChatApp(App):
    def on_mount(self) -> None:
        if sys.platform != "win32":
            asyncio.get_running_loop().add_signal_handler(
                signal.SIGTERM,
                lambda: self.exit(return_code=143),
            )

    # Your compose(), stream_reply(), etc.

if __name__ == "__main__":
    app = ChatApp()
    app.run()
    sys.exit(app.return_code)
```

Merge that registration into your existing `on_mount()`. Calling `exit()` lets Textual’s normal shutdown restore terminal modes, cursor, and screen buffer. Don’t emit terminal-reset sequences from a signal handler. `SIGKILL` (`kill -9`) cannot be handled.

Verify with a long streamed reply: the view should follow, scrolling up should release follow mode, and `kill <pid>` from another terminal should restore a usable shell and exit with status 143.