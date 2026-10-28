Use Textual 8’s **Markdown streaming API**, anchor the scrolling container, and route SIGTERM through `App.exit()`.

Adapt these methods into your app:

```python
import asyncio
import signal
import sys

from textual import work
from textual.app import App
from textual.containers import VerticalScroll
from textual.widgets import Markdown


class ChatApp(App):
    def on_mount(self) -> None:
        # Unix: arrange graceful shutdown on `kill <pid>`.
        if sys.platform != "win32":
            asyncio.get_running_loop().add_signal_handler(
                signal.SIGTERM,
                lambda: self.exit(return_code=143),
            )

    @work(exclusive=True, group="reply")
    async def stream_reply(self, chunks) -> None:
        # These IDs refer to your existing mounted widgets.
        transcript = self.query_one("#transcript", VerticalScroll)
        reply = self.query_one("#reply", Markdown)

        transcript.anchor()
        stream = Markdown.get_stream(reply)
        try:
            async for chunk in chunks:
                await stream.write(chunk)
        finally:
            await stream.stop()


if __name__ == "__main__":
    app = ChatApp()
    app.run()
    sys.exit(app.return_code)
```

- **Stream fragments:** pass only each new text delta to `stream.write()`, rather than the accumulated reply. `get_stream()` batches updates when rendering falls behind, avoiding whole-document updates for every token. `stop()` flushes queued text, including when the worker is cancelled or fails.
- **Follow the tail:** call `anchor()` on the container that actually scrolls. It follows growing content until the user scrolls up. Call it again from a “Follow latest” action to resume; calling it on every token would fight the user.
- **Restore the terminal:** Textual 8 does not install a SIGTERM handler. The event-loop callback above calls `exit()`, allowing Textual’s normal shutdown to restore terminal modes. Avoid manual terminal escape sequences or terminal restoration inside a signal handler. SIGKILL (`kill -9`) cannot be handled.

Keep the LLM client asynchronous; a blocking token iterator still freezes the UI.

Verify with a long reply: it should follow initially, stay put when you scroll up, and flush its final text. Then send `kill <pid>` from another terminal and confirm the shell’s echo and cursor behave normally.