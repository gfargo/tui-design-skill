There's no code in the working directory, so here are general fixes you can adapt.

## 1. Streaming into `Markdown`

`markdown.update(full_text)` re-parses and rebuilds the whole document on every token, so each update costs more as the reply grows. Use `Markdown.get_stream()` instead. It returns a `MarkdownStream` that buffers fragments, batches them, and only re-renders the blocks that changed. To make the view follow new text, call `anchor()` on the scrolling container once. That keeps it pinned to the bottom as content grows. If the user scrolls up, it stops following, and it starts again when they scroll back to the bottom.

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

    @work
    async def stream_reply(self, prompt: str) -> None:
        markdown = self.query_one("#reply", Markdown)
        stream = Markdown.get_stream(markdown)
        try:
            async for token in llm_stream(prompt):  # your LLM client
                await stream.write(token)            # write the fragment, not the full text
        finally:
            await stream.stop()                      # flush remaining buffered text
```

Key points:
- Pass each **delta** (the new token) to `write()`, not the accumulated text.
- Always call `stream.stop()` (in a `finally`) so the last chunk gets rendered.
- For a multi-message chat, mount a new `Markdown` per reply into the `VerticalScroll` and stream into that one. The anchor still applies.

## 2. SIGTERM leaving the terminal broken

Textual puts the terminal into raw mode and the alternate screen, and turns on mouse reporting. It undoes all of that during a normal shutdown. Python's default SIGTERM behaviour kills the process immediately, so that cleanup never runs. The fix is to turn SIGTERM into a normal `app.exit()`:

```python
import asyncio
import signal

class ChatApp(App):
    def on_mount(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGHUP):
            loop.add_signal_handler(sig, self.exit)
        self.query_one("#chat", VerticalScroll).anchor()
```

`add_signal_handler` runs the callback on the event loop, so it's safe to call `self.exit` from it. The app then shuts down the usual way and restores the terminal. SIGHUP is included so closing the terminal window is handled cleanly too.

This won't help with `kill -9` (SIGKILL), because SIGKILL can't be caught. If a terminal does end up broken, run:

```sh
reset
# or, more targeted:
stty sane; printf '\e[?1049l\e[?1000l\e[?1002l\e[?1003l\e[?1006l\e[?25h'
```

If you share your app file, I can apply both changes to it directly.
