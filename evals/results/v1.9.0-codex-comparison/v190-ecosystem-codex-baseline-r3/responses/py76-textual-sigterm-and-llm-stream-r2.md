Use Textual’s Markdown streaming API, anchor the scrolling container, and route SIGTERM through `App.exit()` so Textual can restore the terminal.

```python
import asyncio
import signal

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown


class ChatApp(App):
    CSS = """
    #conversation { height: 1fr; }
    Markdown { height: auto; }
    """

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="conversation"):
            yield Markdown("", id="reply")

    def on_mount(self) -> None:
        # Follow growing content; scrolling up releases the anchor.
        self.query_one("#conversation", VerticalScroll).anchor()

        # Unix: schedule a normal Textual shutdown on SIGTERM.
        asyncio.get_running_loop().add_signal_handler(
            signal.SIGTERM, self.exit
        )

    @work
    async def stream_reply(self) -> None:
        markdown = self.query_one("#reply", Markdown)

        async with markdown.get_stream() as stream:
            async for delta in your_llm_token_iterator():
                await stream.write(delta)  # Only the new text.


if __name__ == "__main__":
    ChatApp().run()
```

- **Streaming:** `get_stream()` buffers incoming chunks and manages incremental Markdown updates. Pass each delta once; repeatedly passing the accumulated reply duplicates work. Exiting the context flushes the remaining text.
- **Following:** anchor the `VerticalScroll` that owns the scrollbar. Its Markdown child must be allowed to grow.
- **Shutdown:** `self.exit()` lets Textual unwind normally and restore terminal settings. Avoid `os._exit()` or raising `SystemExit` in the signal handler. `SIGKILL` (`kill -9`) cannot be handled.

If the terminal is already broken, run `reset` or `stty sane`.

I couldn’t access the live Textual documentation from this environment to independently verify the exact 8.x API signatures.