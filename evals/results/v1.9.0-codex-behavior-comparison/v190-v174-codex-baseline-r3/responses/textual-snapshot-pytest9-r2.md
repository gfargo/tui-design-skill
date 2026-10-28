You’re likely hitting **two separate compatibility changes**.

**The `.raw` files come from Syrupy’s API change.** In Syrupy 5, these extension members became public:

```text
_file_extension                    → file_extension
_read_snapshot_data_from_location  → read_snapshot_data_from_location
```

Older `pytest-textual-snapshot` code overrides the old names, so Syrupy ignores its SVG customization and falls back to `.raw`. Existing SVG baselines then appear missing. This is documented in the [compatibility patch](https://sources.debian.org/patches/pytest-textual-snapshot/1.1.0-3/).

For pytest 9, use a snapshot plugin build containing that fix and a compatible Syrupy version. **Currently, Syrupy 6 supports pytest 9**; its compatibility table lists Syrupy 4 and 5 as requiring pytest below 9. The upstream [Textual compatibility PR](https://github.com/Textualize/pytest-textual-snapshot/pull/24) is still open, so simply upgrading the published plugin may not resolve it. [Syrupy compatibility table](https://pypi.org/project/syrupy/)

**The async errors need an async pytest plugin and correct fixture handling.**

- pytest **8.4** changed unsupported async tests from warning/skipping to failure.
- pytest **9** turns unhandled async-fixture deprecations into errors.
- `pytest-asyncio` **1.3.0** added pytest 9 support. Its 1.0 release also removed the `event_loop` fixture. [pytest changes](https://docs.pytest.org/en/latest/deprecations.html), [pytest-asyncio changes](https://pytest-asyncio.readthedocs.io/en/stable/reference/changelog.html)

A typical Pilot test should look like:

```python
import pytest

@pytest.mark.asyncio
async def test_navigation():
    async with MyApp().run_test() as pilot:
        await pilot.press("tab")
```

Use `@pytest_asyncio.fixture` for async fixtures in strict mode, or configure `asyncio_mode = "auto"` for an asyncio-only suite.

Keep your existing SVG baselines while fixing the dependency mismatch; `.raw` is a compatibility symptom, not an intended Textual snapshot-format migration.