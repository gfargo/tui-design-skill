I couldn't find a project in the working directory (no `pyproject.toml`, lockfile, conftest, or `__snapshots__`), so I can't check your installed versions. This is based on what I know about these packages. Please confirm it against your `pip list` output.

## 1. Snapshots saved as `.raw` instead of `.svg`

The cause is almost certainly **syrupy**, not pytest itself. `pytest-textual-snapshot` is built on syrupy, and upgrading to pytest 9 probably pulled in syrupy 5 because older syrupy versions cap their pytest version.

The extension that saves Textual snapshots is a subclass of syrupy's `SingleFileSnapshotExtension`. In syrupy 4 it set the file type with a private attribute:

```python
class SVGImageExtension(SingleFileSnapshotExtension):
    _file_extension = "svg"
```

syrupy 5 renamed that to a public `file_extension` attribute. Older `pytest-textual-snapshot` releases still set `_file_extension`, so syrupy 5 ignores it and uses its default, `.raw`. The SVG content is still correct. Only the file name is wrong, which also means your existing `.svg` baselines aren't found, so every test looks new or failing.

**Fix:**
- Upgrade `pytest-textual-snapshot` (and `textual`) to a release that supports syrupy 5. Or, if you need to stay where you are for now, pin `syrupy<5`.
- Delete the stray `.raw` files. Then run `pytest --snapshot-update` only if you actually want to regenerate the baselines. Review the diff before committing.

## 2. Async Pilot tests erroring

There are two separate changes:

- **pytest no longer skips async tests it can't run.** Since 8.4, an `async def` test with no async plugin handling it **fails** instead of being skipped with a warning. If `pytest-asyncio` (or `anyio`) isn't installed, isn't loaded, or isn't set to pick up your tests, every `async with app.run_test() as pilot:` test now errors.
- **pytest-asyncio 1.x is a breaking release**, and it's the line that supports current pytest:
  - The `event_loop` fixture is gone. Any test or fixture that requests `event_loop`, or overrides it in `conftest.py`, will error.
  - Strict mode is the default. Each test needs `@pytest.mark.asyncio`, or you can turn on auto mode in config:
    ```toml
    [tool.pytest.ini_options]
    asyncio_mode = "auto"
    asyncio_default_fixture_loop_scope = "function"
    ```
  - Async fixtures in strict mode need `@pytest_asyncio.fixture`, not `@pytest.fixture`.

## To narrow it down

```sh
pip list | grep -Ei "pytest|syrupy|textual|asyncio|anyio"
pytest -x -q path/to/one_pilot_test.py   # first error message tells you which case
```

What the first error says tells you which problem you have:
- **"async def functions are not natively supported"**: the plugin is missing, or the test isn't marked.
- **"fixture 'event_loop' not found"**: you've hit the pytest-asyncio 1.0 change.

If you send me your `pyproject.toml` and that version list, I can tell you exactly which pins or edits you need.
