There's no code in the working directory, so these are general fixes you can adapt to your app.

## 1. Streaming into `Markdown` without re-rendering everything

Each `update(full_text)` call re-parses the whole document and rebuilds every block, so the work grows with each token. Use `Markdown.get_stream()` instead. It returns a `MarkdownStream` that buffers incoming fragments, combines them between refreshes and only re-parses the tail of the document:

```python
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown


class ChatApp(App):
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="chat"):
            yield Markdown(id="reply")

    def on_mount(self) -> None:
        # Keep the view pinned to the bottom as content grows
        self.query_one("#chat", VerticalScroll).anchor()

    @work
    async def stream_reply(self, prompt: str) -> None:
        markdown = self.query_one("#reply", Markdown)
        stream = Markdown.get_stream(markdown)
        try:
            async for token in llm_tokens(prompt):  # your async token source
                await stream.write(token)  # write the delta, not the full text
        finally:
            await stream.stop()  # flush anything still buffered
```

Key points:
- **Write the new token only.** The stream appends fragments, so passing `full_text` each time would repeat the text.
- If you only need to append without the batching, `await markdown.append(token)` also avoids a full re-parse. `get_stream` is better for fast token rates.
- **Following new text:** `Markdown` doesn't scroll by itself. Its scrollable parent does, so call `anchor()` on that container (`VerticalScroll` above). An anchored container stays scrolled to the bottom as content grows. If the user scrolls up to read, it stops following, and it starts again when they scroll back to the bottom. That's usually what you want in a chat view. For a new message in a chat log, mount a new `Markdown` into the anchored container and stream into it.

## 2. Restoring the terminal on SIGTERM

Textual puts the terminal into raw mode, the alternate screen and mouse tracking, and it undoes all of that on a normal exit. SIGTERM's default action kills the process right away, so that cleanup never runs. The fix is to catch SIGTERM and turn it into a normal `app.exit()`:

```python
import asyncio
import signal


class ChatApp(App):
    def on_mount(self) -> None:
        self.query_one("#chat", VerticalScroll).anchor()
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, self.exit)
        loop.add_signal_handler(signal.SIGHUP, self.exit)  # terminal window closed
```

`loop.add_signal_handler` runs the callback on the event loop, not in a raw signal context, so calling `self.exit()` from it is safe. Textual then shuts down normally and restores the terminal. This works on macOS and Linux; Windows doesn't support `add_signal_handler`.

Some caveats:
- **`kill -9` (SIGKILL) can't be caught.** Nothing will restore the terminal in that case.
- If a worker is blocked (for example, a synchronous HTTP call in a thread worker), shutdown waits for it. Use async clients, or `@work(thread=True, exit_on_error=False)` with cancellation checks, so the app exits quickly.
- To fix a terminal that's already broken, type `reset` and press Enter, even if you can't see what you're typing. If that doesn't work, run `stty sane; printf '\e[?1049l\e[?1000l\e[?1003l\e[?1006l'` to leave the alternate screen and turn off mouse tracking.
