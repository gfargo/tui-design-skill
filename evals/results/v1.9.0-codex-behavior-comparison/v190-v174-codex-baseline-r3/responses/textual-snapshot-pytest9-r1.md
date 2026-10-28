You’re likely hitting **two separate compatibility changes**, rather than a change to Textual’s screenshot format.

**The `.raw` files come from Syrupy.** `pytest-textual-snapshot` 1.1.0 pins Syrupy 4.8.0. Moving to a newer Syrupy to support pytest 9 breaks the plugin’s SVG subclass because Syrupy renamed:

```text
_file_extension                    → file_extension
_read_snapshot_data_from_location  → read_snapshot_data_from_location
```

The old overrides are ignored, so Syrupy falls back to `.raw` and skips the plugin’s SVG normalization. [Upstream PR #24](https://github.com/Textualize/pytest-textual-snapshot/pull/24/files) fixes both names and updates the dependency. Use a plugin release or patched fork containing that fix; upgrading Syrupy alone is insufficient. A temporary rollback is `pytest<9` with the plugin’s pinned `syrupy==4.8.0`.

**The async failures depend on the error message:**

- **“async def functions are not natively supported”**: install/enable `pytest-asyncio` and mark async tests. Unhandled async tests began failing instead of being skipped in **pytest 8.4**, so this may surface when jumping directly to 9. [pytest changelog](https://docs.pytest.org/en/8.4.x/changelog.html)
- **“requested an async fixture … with no plugin or hook that handled it”**: pytest 9 turns the earlier warning into an error. With pytest-asyncio’s default **strict mode**, async fixtures need `@pytest_asyncio.fixture`, and tests need `@pytest.mark.asyncio`. [Async discovery rules](https://pytest-asyncio.readthedocs.io/en/stable/concepts.html)

For example:

```python
import pytest

@pytest.mark.asyncio
async def test_pilot():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
```

For an asyncio-only suite, you can instead enable automatic handling:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Textual’s `Pilot` provides app interaction; it still needs an async test runner. Without your traceback and installed versions, the snapshot diagnosis is a strong match, while the precise async cause remains conditional.