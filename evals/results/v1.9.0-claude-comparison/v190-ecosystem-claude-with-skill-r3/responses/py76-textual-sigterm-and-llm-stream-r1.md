Both problems have a fix that's built into Textual.

## 1. Streaming: append fragments instead of re-rendering the whole reply

`markdown.update(full_text)` re-parses and rebuilds the whole document on every token, so each update costs more as the reply grows. Textual's `MarkdownStream` adds only the new fragment. When the widget falls behind, it merges queued fragments into one append, at roughly 20 appends a second. To make the view follow the new text, call `anchor()` on the scroll container. It keeps the view pinned to the bottom until the user scrolls up, then stops following so they can read earlier text.

```python
from textual import work
from textual.containers import VerticalScroll
from textual.widgets import Markdown

@work(exclusive=True)
async def stream_reply(self, chunks) -> None:
    self.query_one(VerticalScroll).anchor()
    stream = Markdown.get_stream(self.query_one(Markdown))
    try:
        async for chunk in chunks:      # pass the token delta, not the accumulated text
            await stream.write(chunk)
    finally:
        await stream.stop()             # flushes queued fragments, even on cancel or error
```

Things to check:
- **Write the delta, not the full text.** If your loop builds `full_text += token`, pass `token` to `stream.write()`. Keep `full_text` only if you need it for history.
- **Put the `Markdown` inside the container you anchor** (a `VerticalScroll` here). Calling `anchor()` on the wrong widget does nothing.
- **Run it in a worker.** `@work` keeps the event loop free so input stays responsive. `exclusive=True` cancels an older stream when a new one starts. The `finally` block makes sure `stop()` runs when that happens.
- **If your LLM client is synchronous** and you're using a thread worker (`@work(thread=True)`), don't touch the widget directly from the thread. Use `self.app.call_from_thread(...)`, or keep the stream loop async and read the client's async iterator.

## 2. SIGTERM: send it through Textual's normal exit path

Textual handles Ctrl+C and `ctrl+q` but installs no SIGTERM handler. Python's default response to SIGTERM kills the process immediately, so the driver never gets to leave raw mode, switch off the alternate screen, show the cursor again or turn off mouse reporting.

The fix is to have the running asyncio loop call `self.exit()` when SIGTERM arrives. Textual then shuts down normally and the driver restores the terminal:

```python
import asyncio
import signal
import sys
from textual.app import App

class ChatApp(App):
    def on_mount(self) -> None:
        if sys.platform != "win32":     # add_signal_handler raises NotImplementedError on Windows
            asyncio.get_running_loop().add_signal_handler(
                signal.SIGTERM, lambda: self.exit(return_code=143))

if __name__ == "__main__":
    app = ChatApp()
    app.run()
    sys.exit(app.return_code or 0)     # 143 = 128 + SIGTERM, so supervisors see a signal exit
```

Why it's done this way:
- **Use `loop.add_signal_handler`, not `signal.signal`.** A `signal.signal` handler can run in the middle of a frame write. If you try to restore the terminal from there, you compete with the driver and can still leave the terminal broken. The loop-based callback runs between tasks, so the normal shutdown runs in full.
- **`return_code` doesn't set the process exit status by itself.** You need the `sys.exit(app.return_code)` after `run()` for the 143 to reach the shell or supervisor.
- **This doesn't cover `kill -9` (SIGKILL).** Nothing can clean up after that. If it happens, `reset` (or `stty sane`) restores the terminal.
- **A stream in progress when SIGTERM arrives** gets cancelled during shutdown. The `finally: await stream.stop()` from part 1 covers that too.

## Checking the fixes

- **Streaming:** in a headless `App.run_test()`, feed a fake async generator of chunks. Assert that the rendered Markdown matches the joined chunks and that the scroll position is at the bottom. Then scroll up in the middle of the stream and assert it stays where you put it.
- **SIGTERM:** do one manual or PTY smoke test. Start the app in a terminal, run `kill <pid>` from another, then check that `echo $?` prints 143 and that typing echoes normally with the cursor visible.
