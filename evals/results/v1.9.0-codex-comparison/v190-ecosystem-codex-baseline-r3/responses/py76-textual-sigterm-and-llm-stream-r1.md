Use a Markdown stream for incremental rendering, anchor the **scrolling container**, and handle SIGTERM by calling `App.exit()`.

```python
import asyncio
import signal

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown


class ChatApp(App):
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="transcript"):
            yield Markdown("", id="reply")

    def on_mount(self) -> None:
        # Follow content as its height grows.
        self.query_one("#transcript", VerticalScroll).anchor()

        # POSIX: let Textual shut down and restore the terminal.
        asyncio.get_running_loop().add_signal_handler(
            signal.SIGTERM, self.exit
        )

    @work
    async def stream_reply(self) -> None:
        markdown = self.query_one("#reply", Markdown)

        async with markdown.get_stream() as stream:
            async for chunk in your_llm_stream():
                await stream.write(chunk)
```

Call `self.stream_reply()` when you start a reply, replacing `your_llm_stream()` with your async token/chunk iterator.

- **Rendering:** send only the new chunk to `stream.write()`. `get_stream()` batches incremental updates; leaving its async context flushes the remaining text. Don’t also call `update(full_text)`.
- **Scrolling:** `anchor()` keeps the `VerticalScroll` following growing content. Anchoring the Markdown itself won’t control its parent’s viewport.
- **Shutdown:** the SIGTERM callback requests normal Textual shutdown, which restores terminal modes. Avoid `os._exit()` or raising `SystemExit` from the signal handler. SIGKILL (`kill -9`) cannot be handled.

If your terminal is already broken, run `reset` in the shell.

I couldn’t verify the live Textual documentation from this environment; the example assumes Textual 8’s `Markdown.get_stream()` and scrolling `anchor()` APIs.