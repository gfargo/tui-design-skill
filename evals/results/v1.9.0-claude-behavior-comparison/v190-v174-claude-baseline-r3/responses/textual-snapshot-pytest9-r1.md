Your working directory is empty, so I can't see your `pyproject.toml`, lockfile, or test output. What follows is what I know about this upgrade path. I haven't confirmed any of it against your setup.

## 1. Async Pilot tests erroring

This is most likely a pytest behavior change, not a Textual one.

- **pytest 8.4 and later fail async tests that no plugin handles.** Before 8.4, an `async def test_...` with no async plugin was skipped with a warning, so it was easy to miss. Now it fails outright. If `pytest-asyncio` (or `anyio`) isn't installed, or doesn't pick the test up, every `async with app.run_test() as pilot:` test errors.
- **pytest-asyncio may have jumped a major version along with pytest.** pytest-asyncio 1.x removed the `event_loop` fixture and some older loop-scope options. In its default strict mode, each async test also needs `@pytest.mark.asyncio`.

Fix: install a pytest-asyncio release that supports pytest 9. Then either mark each test or turn on auto mode:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Also remove any custom `event_loop` fixture overrides from `conftest.py`.

## 2. Snapshots written as `.raw` instead of `.svg`

`pytest-textual-snapshot` is built on **syrupy**. Syrupy's base single-file extension uses `.raw` by default. Textual's plugin replaces that with its own SVG extension. Getting `.raw` files means syrupy's default is being used instead of Textual's SVG extension. The usual causes:

- **The pytest upgrade pulled in a newer syrupy that your `pytest-textual-snapshot` version doesn't support**, so its extension isn't applied correctly. Upgrade `pytest-textual-snapshot` to a release that lists pytest 9 and your syrupy version as supported, or pin syrupy back to the version it was tested with.
- **Tests use syrupy's plain `snapshot` fixture instead of `snap_compare`.** Only `snap_compare(app_or_path, ...)` produces SVGs.
- **The plugin isn't loading.** `pytest --version -VV` or the plugin list in the session header should show `textual-snapshot`.

## Checks to run

```sh
pip show pytest pytest-asyncio syrupy pytest-textual-snapshot textual
pytest -p no:cacheprovider -q 2>&1 | head -50   # see the first actual error
```

When it's fixed, delete the stray `.raw` files and the `__snapshots__` entries that came with them. Then regenerate with `pytest --snapshot-update` and review the SVG diffs before committing.

If you paste those version numbers and the first traceback, or run me from the project directory, I can tell you which of these is actually happening.
