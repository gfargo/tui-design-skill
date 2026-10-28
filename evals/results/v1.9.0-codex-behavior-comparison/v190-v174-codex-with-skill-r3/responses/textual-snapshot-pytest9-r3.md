These are two separate testing-stack issues, described in the tui-design skill’s Python reference.

**The `.raw` files likely mean your snapshot plugin was downgraded.** `pytest-textual-snapshot==1.1.0` pins `syrupy==4.8.0`, which requires `pytest<9`. Resolving dependencies with pytest 9 can select the older `pytest-textual-snapshot==1.0.0`, which writes `.raw` snapshots instead of `.svg`.

Restore the compatible stack and keep those constraints in your test dependencies:

```sh
python -m pip install "pytest>=8.4,<9" \
  "pytest-textual-snapshot==1.1.0" pytest-asyncio
python -m pip check
```

**Async Pilot tests need an async pytest plugin and explicit handling.** Textual’s `run_test()` provides the headless app harness; it doesn’t make pytest execute async tests. Install `pytest-asyncio`, then either enable automatic handling in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Or mark each test, preserving pytest-asyncio’s default strict mode:

```python
import pytest

@pytest.mark.asyncio
async def test_app():
    async with MyApp().run_test(size=(80, 24)) as pilot:
        await pilot.press("tab")
        await pilot.pause()
```

If you use strict mode, async fixtures also need `@pytest_asyncio.fixture`.

Check your installed versions with:

```sh
python -m pip show pytest pytest-textual-snapshot syrupy pytest-asyncio
```

The `.raw` symptom points to dependency resolution. An “async def functions are not natively supported” error points to missing or unconfigured async test support. Keep your SVG baselines while fixing the environment.