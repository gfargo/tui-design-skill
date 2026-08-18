No. `httpx.get(url)` is synchronous: it blocks and its result is not awaitable. Use an `AsyncClient` inside an async Textual worker.

```python
import httpx

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Static


class FetchApp(App):
    def compose(self) -> ComposeResult:
        yield Static("Loading…", id="result")

    def on_mount(self) -> None:
        self.fetch("https://example.com")

    @work
    async def fetch(self, url: str) -> None:
        result = self.query_one("#result", Static)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as error:
            result.update(f"Request failed: {error}")
        else:
            result.update(response.text)


if __name__ == "__main__":
    FetchApp().run()
```

`@work` keeps the UI responsive; because this is an async worker (not `thread=True`), updating `Static` directly is safe. `raise_for_status()` turns 4xx/5xx responses into catchable `HTTPStatusError`s. [Textual workers](https://textual.textualize.io/guide/workers/) and [HTTPX async support](https://www.python-httpx.org/async/) document this pattern.
