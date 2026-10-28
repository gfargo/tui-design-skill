There's no project code in this directory, so here are the general fixes. Adapt the widget IDs to match your app.

## 1. Streaming: use `MarkdownStream` and anchor the scroll container

Calling `update(full_text)` on every token re-parses and rebuilds the whole document each time, so the cost grows as the reply gets longer. Textual has a streaming API for this. `Markdown.get_stream()` returns a `MarkdownStream` that buffers fragments, groups tokens that arrive close together, and only re-renders the last block that changed.

To make the view follow new text, put the `Markdown` in a scroll container and call `anchor()` on the container. An anchored container stays scrolled to the bottom as content grows. If the user scrolls up to read, it stops following until they return to the bottom, which is usually what you want.

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
        self.query_one("#chat", VerticalScroll).anchor()
        self.stream_reply("...prompt...")

    @work(exclusive=True)
    async def stream_reply(self, prompt: str) -> None:
        markdown = self.query_one("#reply", Markdown)
        stream = Markdown.get_stream(markdown)
        try:
            async for token in llm_tokens(prompt):   # your async token source
                await stream.write(token)            # append only the new fragment
        finally:
            await stream.stop()                      # flush remaining buffered text
```

Notes:
- Pass only the **new token** to `write()`, not the accumulated text.
- Always call `stream.stop()`. The `finally` block makes sure the last fragment is flushed if the worker is cancelled.
- If your LLM client is synchronous, use `@work(thread=True)` and call `self.call_from_thread(...)` to write into the stream, or wrap the client in an async generator.
- For a chat log with several messages, mount a new `Markdown` per reply inside the anchored container. The anchor will keep following the newest one.

## 2. SIGTERM leaves the terminal broken

While the app runs, Textual puts the terminal in raw mode and the alternate screen, and enables mouse tracking. Its driver undoes all of this on a normal exit. SIGTERM's default action kills the process immediately, so that cleanup never runs. The fix is to handle SIGTERM and turn it into a normal `app.exit()`:

```python
import asyncio
import signal

class ChatApp(App):
    def on_mount(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGHUP):
            loop.add_signal_handler(sig, self.exit)
        # ... anchor / start streaming as above
```

`add_signal_handler` runs the callback in the event loop, so it's safe to call `self.exit()` there. The app then shuts down normally: workers are cancelled (your `finally: await stream.stop()` runs) and the terminal is restored. SIGHUP covers a closed terminal window. `add_signal_handler` is Unix-only, which is fine on macOS.

Two limits:
- **`kill -9` (SIGKILL) can't be caught.** If that happens, or the app crashes hard, run `reset` (or `stty sane`) in the broken terminal to recover.
- If you run cleanup after `app.run()` returns, keep it short and don't block, so a supervisor sending SIGTERM doesn't time out and escalate to SIGKILL.
