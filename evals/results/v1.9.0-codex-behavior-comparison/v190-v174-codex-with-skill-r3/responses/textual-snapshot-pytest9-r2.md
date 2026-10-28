You’re likely hitting two separate test dependency issues described in the tui-design skill’s Python reference.

**The `.raw` files come from a snapshot plugin downgrade.** `pytest-textual-snapshot==1.1.0` pins `syrupy==4.8.0`, which requires `pytest<9`. When resolving against pytest 9, pip can fall back to `pytest-textual-snapshot==1.0.0`, which writes `.raw` snapshots instead of `.svg`.

For the documented compatible stack, pin:

```sh
python -m pip install "pytest>=8.4,<9" \
  "pytest-textual-snapshot==1.1.0" "pytest-asyncio"
```

Update your dependency declarations and lockfile too, so the next install preserves those constraints.

**Async Pilot tests need `pytest-asyncio` and explicit async handling.** Its default strict mode requires `@pytest.mark.asyncio` on each async test. Alternatively, enable automatic handling in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Then a Pilot test can run as:

```python
async def test_app():
    app = MyApp()
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.press("tab")
        await pilot.pause()
        # Assert application state here.
```

Check what actually resolved with:

```sh
python -m pip show pytest pytest-textual-snapshot syrupy pytest-asyncio
python -m pip check
```

If your async error says “async def functions are not natively supported,” the plugin installation or async configuration is the relevant fix. A different traceback may indicate another issue.