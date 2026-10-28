Two things are going on, and they have separate causes.

## 1. `.raw` snapshots: the resolver installed an older pytest-textual-snapshot

pytest-textual-snapshot's latest release is 1.1.0 (January 2025). It pins `syrupy==4.8.0`, and that syrupy version requires `pytest<9`. When you require pytest 9, pip can't install 1.1.0. It falls back to **pytest-textual-snapshot 1.0.0** without telling you, and 1.0.0 writes snapshots as `.raw` files instead of `.svg`.

You can check this:

```sh
pip show pytest-textual-snapshot syrupy   # expect 1.0.0 / a non-4.8.0 syrupy
```

**Fix:** pin pytest below 9 for any suite that uses snapshots, until pytest-textual-snapshot releases a version that supports pytest 9:

```toml
# pyproject.toml
[dependency-groups]   # or [project.optional-dependencies].dev
dev = [
  "pytest>=8.4,<9",
  "pytest-textual-snapshot>=1.1.0",
  "pytest-asyncio>=1.4",
]
```

The `>=1.1.0` lower bound matters. If something pulls pytest 9 in again, installation fails with an error instead of quietly downgrading. The `>=8.4` floor is there because pytest-asyncio 1.4 needs pytest 8.4 or later. After reinstalling, delete the `.raw` files and run `pytest --snapshot-update` once to regenerate the SVG baselines. Review the new SVGs before you commit them.

## 2. Async Pilot tests: unhandled `async def` tests now fail

Pytest can't run `async def` tests by itself. pytest-asyncio has to claim each one. Its default **strict mode** only claims tests marked with `@pytest.mark.asyncio`. Any unmarked async test fails with:

```
async def functions are not natively supported
```

If you upgraded from pytest older than 8.4, there's a likely catch: those versions only warned and skipped unhandled async tests. Unmarked Pilot tests may have been "passing" by being skipped, and now they show up as failures. I'm inferring this from your symptoms. It's worth checking old CI logs for skip warnings.

**Fix:** use auto mode, as Textual's own test suite does:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

You can also mark each test instead:

```python
@pytest.mark.asyncio
async def test_button_click():
    app = HelloApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.click("#go")
        await pilot.pause()
        assert app.query_one("#greeting", Label).content == "Button pressed!"
```

Also make sure `pytest-asyncio` is actually installed in the test environment. If it's missing, you get the same error.

## In short
- **Pin `pytest>=8.4,<9`**, require `pytest-textual-snapshot>=1.1.0`, and regenerate your snapshots. This fixes the `.raw` files.
- **Set `asyncio_mode = "auto"`** and make sure pytest-asyncio ≥1.4 is installed. This fixes the async errors.

If the async errors continue after these changes, paste the traceback.
