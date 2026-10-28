Both problems have a direct fix in Textual 8.

## 1. Streaming: append chunks to a `MarkdownStream` and anchor the scroll container

`markdown.update(full_text)` re-parses and rebuilds the whole document on every token. That gets slower as the reply gets longer. Instead, get a stream from the widget and write only the new chunks to it. `Markdown.get_stream()` batches fragments when the widget can't keep up (it renders about 20 appends a second), so a fast model doesn't flood it.

The view doesn't follow the new text because nothing tells it to. Call `anchor()` on the scroll container that holds the Markdown. The view then stays pinned to the bottom as content grows, and stops following when the user scrolls up to read.

```python
from textual import work
from textual.containers import VerticalScroll
from textual.widgets import Markdown

@work(exclusive=True)
async def stream_reply(self, chunks) -> None:
    self.query_one(VerticalScroll).anchor()
    stream = Markdown.get_stream(self.query_one(Markdown))
    try:
        async for chunk in chunks:      # pass each token/delta, not the full text
            await stream.write(chunk)
    finally:
        await stream.stop()             # flushes any queued text, even on cancel/error
```

Things to check:
- **Write deltas, not the running total.** If your LLM client gives you the accumulated text, take the new part with `full[len(prev):]` before calling `write`.
- **The Markdown must be inside a scrolling container**, e.g. `VerticalScroll`. Anchor that container, not the Markdown widget.
- **Keep `stream.stop()` in `finally`.** Without it, cancelling the reply (for example when `exclusive=True` replaces it with a newer one) can lose the last batch of text.
- **Run the stream in an async worker**, as above, so the event loop isn't blocked. If your client library is synchronous and runs in a thread worker, send the chunks back through `self.app.call_from_thread(...)` instead.

## 2. SIGTERM: send it through `App.exit()`

Textual installs no SIGTERM handler. By default, `kill <pid>` ends the process immediately and the driver never restores the terminal, so raw mode, the alternate screen and mouse capture are left on. The fix is to have the running asyncio loop handle SIGTERM by calling `self.exit()`. Shutdown then follows the normal path, which restores the terminal.

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
    sys.exit(app.return_code)  # pass 143 (128 + SIGTERM) on to the process
```

Things to check:
- **Use `loop.add_signal_handler`, not `signal.signal`.** A `signal.signal` handler can run at any point in your code, so you shouldn't restore the terminal from it. The loop handler runs between tasks, where calling `exit()` is safe.
- **`return_code` doesn't set the process exit status by itself.** You need the `sys.exit(app.return_code)` after `run()` so that supervisors and scripts see 143.
- **SIGKILL (`kill -9`) can't be handled.** If that happens, run `reset` (or `stty sane`) in the shell.

To check it, start the app, run `kill <pid>` from another shell, and confirm that your prompt comes back usable and `echo $?` prints 143. In a test, run a long fake chunk generator and check that cancelling the worker still shows the final text, which confirms that `stop()` flushes.
