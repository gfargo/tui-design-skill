You don't need to pin either. Chalk works with plain `require()` on modern Node 22. Ink is the one exception, and you load it with a dynamic `import()` instead of downgrading.

**Check your Node 22 minor first.** `require()` of ES modules works without a flag from **Node 22.12** onward. On 22.0–22.11 it fails, so set `"engines": { "node": ">=22.12" }`. Commander 15 also needs 22.12+, and listr2 11 needs 22.13+.

**Chalk 5/6, commander, @clack/prompts, @inquirer/prompts: just `require()` them.** These are ES modules that load synchronously, so CommonJS can load them directly. The only catch is that a default export comes back as `.default`:

```js
const chalk = require('chalk').default;          // chalk 6 (Node ≥ 22)
const { Command } = require('commander');        // v15
const { intro, text, outro } = require('@clack/prompts');
```

**Ink: use `await import()`.** Ink depends on Yoga, which uses top-level await. Node can't load that synchronously, so `require('ink')` throws `ERR_REQUIRE_ASYNC_MODULE` on Ink 6.8 through 8. Pinning an old Ink isn't the fix. Load it with a dynamic import from your CommonJS code:

```js
// cli.js (CommonJS)
async function runTui() {
  const { render } = await import('ink');
  const React = require('react');               // React is still CJS
  const { App } = require('./app');              // your compiled components
  const { waitUntilExit } = render(React.createElement(App));
  await waitUntilExit();
}
```

This also loads Ink only when the TUI actually runs, so `--help` and `--version` start faster. Your components can stay CommonJS if they get the Ink primitives (`Box`, `Text`, hooks) from that same dynamic import, either passed in or set up in an async init. If that gets messy, bundling with esbuild or tsup is the other option the skill suggests. Either way, Ink 8 needs React ≥ 19.3, and Ink 7 needs ≥ 19.2.

**When old majors still make sense:** only if part of your deployment is stuck on Node 20 or below 22.12. Then the last compatible lines are chalk 5, commander 14 (security fixes until May 2027) and Ink 6. Treat those as a temporary bridge, not where you settle.

All of this comes from the skill's "Runtime floors and ESM" section (`references/ecosystem-typescript.md:30-41`). I didn't run anything against your project.
