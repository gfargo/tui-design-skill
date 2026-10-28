The snapshot problem has one known cause. The async failures probably come from the same dependency resolution, but I can't confirm that without seeing your installed versions and the error text.

## Snapshots: `.raw` instead of `.svg`

The latest release of pytest-textual-snapshot is 1.1.0, from January 2025. It pins `syrupy==4.8.0`, and that version of syrupy requires `pytest<9`. pip can't install 1.1.0 alongside pytest 9, so it quietly falls back to **pytest-textual-snapshot 1.0.0**. Version 1.0.0 saves snapshots in syrupy's raw format, which is why you're getting `.raw` files.

**The fix is to stay on pytest 8 for snapshot suites until pytest-textual-snapshot ships a release that supports pytest 9:**

```toml
[dependency-groups]   # or [project.optional-dependencies] test = [...]
test = [
  "pytest>=8.4,<9",
  "pytest-asyncio>=1.4",
  "pytest-textual-snapshot>=1.1.0",
]
```

Putting `>=1.1.0` on pytest-textual-snapshot makes any future conflict fail at install time instead of silently giving you an older version. Then:
- Delete the `.raw` files that 1.0.0 wrote in `__snapshots__/`.
- Rerun with `pytest --snapshot-update`.
- Check that `.svg` files come back.

## Async Pilot tests erroring

The upgrade probably also changed which pytest-asyncio version is installed, or dropped it. Without the plugin, every `async def` test fails with **"async def functions are not natively supported"**. Two things to check:

1. **Is the plugin installed, and which version?** Run `pip show pytest-asyncio` or `uv pip list | grep -i asyncio`. pytest-asyncio 1.4 requires pytest 8.4 or later. With the pin above you should get pytest 8.4.x and pytest-asyncio 1.4+ together.
2. **Is it in auto mode?** pytest-asyncio defaults to strict mode, which fails any `async def` test that isn't marked. Textual's own test suite uses auto mode:

   ```toml
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   ```

   The alternative is to mark each test with `@pytest.mark.asyncio`.

If both are fine and the tests still error, send me the traceback and the output of `pip list | grep -iE "pytest|syrupy|textual"`. The cause would then be something other than these two.

One more thing that commonly trips up Pilot tests: `run_test()` runs at 80×24 with notifications and tooltips turned off. Any assertion on a `notify()` toast needs `run_test(notifications=True)`.
