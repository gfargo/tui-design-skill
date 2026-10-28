You’re likely seeing **two dependency-compatibility issues**, rather than a change to Textual’s rendering.

- **`.raw` snapshots:** Textual’s snapshot plugin uses **Syrupy** to store SVGs. `.raw` is Syrupy’s generic raw-file extension; seeing it usually means the installed `pytest-textual-snapshot` and Syrupy versions aren’t agreeing on the SVG snapshot extension. Check those versions together. The file may still contain SVG XML—open one and look for `<svg`.
- **Async Pilot errors:** **pytest 9 makes unsupported async tests an error**; older pytest versions could warn and skip them. `App.run_test()` supplies the Textual test environment, but an async pytest plugin still needs to run your `async def` test. Pytest 9 also errors when a synchronous test requests an async fixture that no plugin handles.

For asyncio-based Pilot tests, install a pytest-9-compatible `pytest-asyncio`, then either mark tests explicitly:

```python
import pytest

@pytest.mark.asyncio
async def test_app():
    async with MyApp().run_test() as pilot:
        await pilot.press("tab")
```

Or enable automatic handling:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

With the default strict mode, async fixtures should use `@pytest_asyncio.fixture`.

Check the actual dependency set with:

```sh
python -m pip show pytest pytest-asyncio pytest-textual-snapshot syrupy
python -m pip check
```

**Don’t regenerate all your snapshots yet.** Resolve the snapshot-plugin/Syrupy compatibility first. I couldn’t verify current release notes from this environment; the four versions above and the async traceback would let me identify the exact incompatibility.