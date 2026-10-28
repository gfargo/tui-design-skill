Use Textual 8’s Markdown streaming API, anchor the scrolling container, and route SIGTERM through `App.exit()`.

```python
import asyncio
import signal
import sys

from textual import work
from textual.app import App
from textual.containers import VerticalScroll
from textual.widgets import Markdown


class ChatApp(App):
    # Existing compose() mounts:
    # VerticalScroll(id="chat") containing Markdown(id="reply")

    def on_mount(self) -> None:
        if sys.platform != "win32":
            asyncio.get_running_loop().add_signal_handler(
                signal.SIGTERM,
                lambda: self.exit(return_code=143),
            )

    @work(exclusive=True, group="reply")
    async def stream_reply(self, chunks) -> None:
        self.query_one("#chat", VerticalScroll).anchor()
        markdown = self.query_one("#reply", Markdown)
        stream = Markdown.get_stream(markdown)

        try:
            async for chunk in chunks:
                await stream.write(chunk)  # New text only
        finally:
            await stream.stop()  # Flush queued text


if __name__ == "__main__":
    app = ChatApp()
    app.run()
    sys.exit(app.return_code)
```

- **Performance:** `Markdown.get_stream()` batches incoming fragments instead of repeatedly processing the entire reply. Pass token deltas, not accumulated `full_text`. Use an empty Markdown widget for each new reply.
- **Scroll following:** call `anchor()` on the container that actually scrolls. It follows growing content until the user scrolls up; avoid forcing `scroll_end()` on every token.
- **Terminal cleanup:** Textual 8 installs no SIGTERM handler. The event-loop callback above invokes normal shutdown, allowing Textual to restore terminal modes. Don’t perform terminal restoration directly in a signal handler. SIGKILL (`kill -9`) cannot be cleaned up.

Verify with a long response: it should follow the tail, allow scrolling up without snapping back, and leave the terminal usable after `kill <pid>`.