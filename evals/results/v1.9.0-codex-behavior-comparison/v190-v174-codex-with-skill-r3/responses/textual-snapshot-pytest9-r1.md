Two separate test dependencies explain this, according to the tui-design skill’s [Python testing guidance](/Users/gfargo/dev/gfargo/tui-design-skill/.claude/worktrees/eloquent-ritchie-f2f1c8/plugins/tui-design/skills/tui-design/references/ecosystem-python.md).

**The `.raw` files indicate a snapshot-plugin downgrade.** `pytest-textual-snapshot==1.1.0` pins `syrupy==4.8.0`, which requires `pytest<9`. With pytest 9, pip can resolve to the older `pytest-textual-snapshot==1.0.0`, which writes `.raw` snapshots instead of `.svg`.

Restore the compatible stack:

```sh
python -m pip install "pytest>=8.4,<9" "pytest-textual-snapshot==1.1.0" pytest-asyncio
python -m pip check
```

Update your dependency declarations and lockfile with those constraints too.

**Async Pilot tests require `pytest-asyncio` and async-test configuration.** If the error says “async def functions are not natively supported,” ensure the plugin is installed, then either mark tests with `@pytest.mark.asyncio` or enable automatic handling in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Pilot tests still use the same pattern:

```python
async def test_app():
    async with MyApp().run_test(size=(80, 24)) as pilot:
        await pilot.press("tab")
        await pilot.pause()
        # Assert application state here.
```

Check the installed versions with `python -m pip show pytest pytest-textual-snapshot syrupy pytest-asyncio`. The snapshot format change comes from dependency resolution; the async error needs its own plugin/configuration fix.