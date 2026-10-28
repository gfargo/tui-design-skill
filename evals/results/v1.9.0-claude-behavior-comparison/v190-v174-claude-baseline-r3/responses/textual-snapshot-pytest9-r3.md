I couldn't check your setup because there's no project in this directory: no `pyproject.toml`, lockfile, or installed packages. What follows is the usual cause of both symptoms. Run the commands at the end to confirm it matches your environment.

## 1. Snapshots saved as `.raw` instead of `.svg`

pytest-textual-snapshot doesn't write files itself. It uses **syrupy**, through a custom `SingleFileSnapshotExtension` subclass that sets the file extension to `svg`. Syrupy's base class defaults that extension to `raw`.

To support pytest 9, you most likely also got a new **major version of syrupy (5.x)**, either pulled in automatically or because the resolver chose it. Syrupy 5 changed how single-file extensions declare their file extension. If your pytest-textual-snapshot was written for syrupy 4, its `svg` setting no longer overrides anything. Syrupy then falls back to `.raw`, and every test treats its snapshot as new or missing.

**Fix (pick one):**
- Upgrade pytest-textual-snapshot to a release that supports syrupy 5 and pytest 9: `pip install -U pytest-textual-snapshot syrupy`
- Or, as a short-term fix, pin `syrupy<5` (only if the version you end up with still works with pytest 9).

Afterwards, delete the stray `__snapshots__/**/*.raw` files. Don't run `--snapshot-update` until the extension is fixed, or it will save more `.raw` files and mark your SVGs as unused.

## 2. Async Pilot tests erroring

Two changes usually combine here:

- **pytest no longer skips async tests it can't run.** Since pytest 8.4, an `async def` test with no async plugin to handle it fails instead of being skipped with a warning. Before, these tests may have been quietly skipped, so this error may be the first time you've seen they weren't running.
- **pytest-asyncio has to be ≥ 1.x for pytest 9.** Older versions break with errors from internal pytest APIs, typically at collection time. pytest-asyncio 1.0 also **removed the `event_loop` fixture**. Any conftest that overrides or requests `event_loop` will now error.

**Fix:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"                      # or mark tests with @pytest.mark.asyncio
asyncio_default_fixture_loop_scope = "function"
```
- `pip install -U pytest-asyncio` (or anyio's plugin with `@pytest.mark.anyio`, if that's what you use).
- Remove any custom `event_loop` fixture. If you need a different loop scope, use `@pytest.mark.asyncio(loop_scope="module")` or the `asyncio_default_fixture_loop_scope` setting.
- Your `async with app.run_test() as pilot:` code itself shouldn't need changes.

## To confirm
```sh
pip list | grep -Ei 'pytest|syrupy|textual'
pytest -x -q path/to/one_async_test.py   # read the first error
```
If you share that output, or point me at the project directory, I can tell you exactly which versions are clashing and what to pin.
