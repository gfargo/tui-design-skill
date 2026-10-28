No, you don't need to pin either. Node 22 can now `require()` most ESM-only packages. Ink is the one exception, and the fix is a single `await import()`, not an old Ink version.

**chalk and similar packages: use the current major and keep `require()`.**
Starting with Node 22.12, CommonJS code can `require()` an ESM package without a flag, as long as that package has no top-level await. That covers chalk 5/6, commander, @clack/prompts, @inquirer/prompts and most of the rest of the modern stack.

```js
const chalk = require('chalk').default;   // ESM default export lives on .default
const { Command } = require('commander');
const { intro, text } = require('@clack/prompts');
```

Set `"engines": { "node": ">=22.12" }`. Versions 22.0–22.11 need `--experimental-require-module`. Some current majors have their own minimums: commander 15 needs ≥ 22.12 and listr2 11 needs ≥ 22.13. For basic colors with no dependency at all, `node:util`'s `styleText` is stable from 22.13.

**Ink: use the current version, but load it with `import()`.**
Ink 6.8 through 8 depend on Yoga, which uses top-level await. So `require('ink')` fails with `ERR_REQUIRE_ASYNC_MODULE`. Pinning an old Ink would avoid the error, but you'd lose years of fixes. Instead, load it with a dynamic import at the point where you start the UI:

```js
// cli.js (CommonJS)
async function runTui() {
  const { render } = await import('ink');
  const React = require('react');            // React itself is still CJS
  const { App } = require('./app');           // App components can stay CJS too
  const { waitUntilExit } = render(React.createElement(App));
  await waitUntilExit();
}
```

As a bonus, this keeps Ink and React out of startup for commands that don't render a TUI, so `--help` and `--version` stay fast. Component files that need Ink's `Box`/`Text` should get them passed in, or be loaded through the same dynamic import. The alternative is to bundle with esbuild or tsup, which removes the problem.

**If you compile with TypeScript:**
- With `"module": "commonjs"`, tsc rewrites `await import('ink')` into `require('ink')`, which brings the error back. Use `"module": "nodenext"` (or `node16`) so the dynamic import stays as written.
- Under `nodenext` with TS 5.8 or later, you can write `import chalk from 'chalk'` in a CJS file, and it compiles to a `require()` that works with require(esm).

**When to pin anyway:** only if part of your deployment can't reach Node 22.12. In that case the last versions that still support Node 20 are Ink 6, chalk 5 and commander 14. Node 20 is end-of-life, so treat that as a temporary bridge.

This is based on the skill's runtime and ESM reference notes; I didn't run anything against your project. If you share your `package.json` and `tsconfig`, I can tell you exactly what to change.
