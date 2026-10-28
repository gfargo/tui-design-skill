Your pytest 9 upgrade didn't change anything in Textual itself. It broke the dependency chain under your snapshot plugin, and it exposed an async setting your suite may have been missing.

## 1. `.raw` files instead of SVGs

- `pytest-textual-snapshot` last shipped **1.1.0** in January 2025. That release pins `syrupy==4.8.0`, and that syrupy version requires `pytest<9`.
- Once you're on pytest 9, pip can't install 1.1.0. Instead of failing, it quietly falls back to **pytest-textual-snapshot 1.0.0**, which uses an older serializer that writes `.raw` snapshots instead of `.svg`.

You can confirm this with:

```sh
pip show pytest-textual-snapshot syrupy pytest
```

If it shows 1.0.0, that's the cause.

**Fix:** pin pytest below 9 for any suite that uses `snap_compare`:

```toml
[project.optional-dependencies]   # or your dev dependency group
dev = [
  "pytest>=8.4,<9",
  "pytest-asyncio>=1.4",
  "pytest-textual-snapshot>=1.1.0",
]
```

The lower bound of 8.4 is there because pytest-asyncio 1.4 needs pytest 8.4 or later. Then delete the stray `.raw` files under `__snapshots__/` and regenerate with `pytest --snapshot-update`. Check the new SVGs before you commit them.

## 2. Async Pilot tests erroring

pytest doesn't run `async def` tests by itself. Since pytest 8.4, an async test that no plugin handles fails with "async def functions are not natively supported" instead of being skipped with a warning. So check these two things:

- **Is pytest-asyncio still installed, and at a version that supports your pytest?** The resolver may have changed it during the same upgrade, so look at `pip show pytest-asyncio` too.
- **Is pytest-asyncio running in strict mode (the default)?** In strict mode, any `async def` test without a marker fails with that same error. Either mark each test with `@pytest.mark.asyncio` or turn on auto mode, which is what Textual's own test suite uses:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

After that, `async with app.run_test(size=(80, 24)) as pilot:` tests should run normally again.

**Summary:** pin `pytest>=8.4,<9` until pytest-textual-snapshot releases a version that supports pytest 9, keep pytest-asyncio at 1.4 or newer, and set `asyncio_mode = "auto"`. If you paste your dependency list or the exact traceback from the async tests, I can tell you which of these is the cause.
