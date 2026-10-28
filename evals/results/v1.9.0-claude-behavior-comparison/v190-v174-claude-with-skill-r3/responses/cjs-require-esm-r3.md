No, you don't need to pin them. On Node 22 you can upgrade both, with one exception for how you load Ink.

**chalk: upgrade and keep `require()`.** Starting with Node 22.12, CommonJS can `require()` ESM-only packages as long as they don't use top-level await. chalk 5/6 qualifies. The only change is that the default export comes back as `.default`:

```js
const chalk = require('chalk').default;
```

The same applies to commander 15, `@clack/prompts`, `@inquirer/prompts`, and other synchronous ESM packages. Pinning older CommonJS versions is no longer necessary. For basic styling with no dependencies, `require('node:util').styleText` is another option.

**Ink: upgrade, but you can't `require()` it.** Ink 6.8 through 8 depend on Yoga, which uses top-level await, so `require('ink')` throws `ERR_REQUIRE_ASYNC_MODULE`. That doesn't mean you need an old Ink. You have two options:

1. **Dynamic import** (works from CommonJS):
   ```js
   async function runTui() {
     const { render } = await import('ink');
     const React = require('react');
     const { App } = require('./ui/app'); // components can require React normally;
                                         // they just can't require('ink') themselves
     const { waitUntilExit } = render(React.createElement(App));
     await waitUntilExit();
   }
   ```
   Component files that use `Box` or `Text` can't `require('ink')` either. Pass Ink's exports into them, or put the TUI code in its own `.mjs` and `import()` that one file. Loading it lazily also keeps `--help` and `--version` fast, because Ink and React only load when the TUI runs.
2. **A bundler** (esbuild or tsup) that builds the TUI entry point, so your source can use `import` syntax throughout.

**Version requirements:**
- You need **Node ≥ 22.12** for `require()` of ESM to work without a flag. Set `"engines": { "node": ">=22.12" }`.
- Ink 7/8 need Node ≥ 22. Ink 8 also needs React ≥ 19.3 (Ink 7 needs ≥ 19.2).
- chalk 6 needs Node ≥ 22.
- If you add listr2 11, it needs Node ≥ 22.13.

So: upgrade chalk and keep `require()`, and upgrade Ink but load it with `await import('ink')` or bundle it.
