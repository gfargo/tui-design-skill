Use **`Markdown.get_stream()` for token deltas**, **`anchor()` on the scrolling container**, and route **SIGTERM to `App.exit()`**.

For streaming, adapt this method to your app:

```python
from textual import work
from textual.containers import VerticalScroll
from textual.widgets import Markdown

@work
async def stream_reply(self):
    markdown = self.query_one("#reply", Markdown)
    container = self.query_one("#chat", VerticalScroll)

    await markdown.update("")  # Once, when starting this reply
    container.anchor()

    stream = Markdown.get_stream(markdown)
    try:
        async for delta in self.llm_chunks():  # Your async token source
            await stream.write(delta)         # Only the new text
    finally:
        await stream.stop()                   # Drain buffered updates
```

`update(full_text)` replaces the document repeatedly. `append(delta)` supports incremental updates; `get_stream()` additionally combines incoming chunks when rendering falls behind. Run the network loop in an async worker so the UI remains responsive. [Markdown documentation](https://textual.textualize.io/widgets/markdown/#textual.widgets.Markdown.get_stream)

Anchor the **container that actually scrolls**, rather than the Markdown child. It follows growing content until the user scrolls away; call `container.anchor()` again for a “follow latest” action. [Anchor documentation](https://textual.textualize.io/api/widget/#textual.widget.Widget.anchor)

For SIGTERM on macOS/Linux, register an event-loop handler inside your app:

```python
import asyncio
import signal

# Methods on your App subclass:
def on_mount(self) -> None:
    asyncio.get_running_loop().add_signal_handler(
        signal.SIGTERM, self.exit
    )

def on_unmount(self) -> None:
    asyncio.get_running_loop().remove_signal_handler(signal.SIGTERM)
```

This schedules normal Textual shutdown, allowing terminal cleanup to run. `self.exit()` is synchronous; don’t await it or replace it with `os._exit()`. Textual 8’s `exit()` posts its normal exit message. [Textual 8 source](https://raw.githubusercontent.com/Textualize/textual/v8.0.0/src/textual/app.py)

`SIGKILL` (`kill -9`) cannot be handled. To recover an already broken terminal, run `reset`.