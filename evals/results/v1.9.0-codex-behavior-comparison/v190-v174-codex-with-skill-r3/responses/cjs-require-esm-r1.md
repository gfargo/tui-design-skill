No—you can keep your CLI CommonJS without pinning both libraries. **Use Node 22.12+ as the minimum**, since the minor version matters.

| Package | Loading from CommonJS |
|---|---|
| Modern Chalk (ESM-only) | `const chalk = require('chalk').default` |
| Modern Ink | Use `await import('ink')`; synchronous `require('ink')` fails because Yoga uses top-level `await`. |

For example, in a `.cjs` entry point:

```js
const React = require('react');
const chalk = require('chalk').default;

async function main() {
  const {render, Text} = await import('ink');

  console.log(chalk.green('Starting'));
  const app = render(
    React.createElement(Text, null, 'Hello from CommonJS')
  );
  await app.waitUntilExit();
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

Node’s `require(ESM)` support only works when the **entire dependency graph is synchronous**. Ink’s Yoga dependency breaks that condition, producing `ERR_REQUIRE_ASYNC_MODULE`.

My recommendation: keep CommonJS, raise your runtime floor to **22.12+**, and dynamically import Ink at the UI entry point. Match Ink’s React peer dependency when upgrading. Pin older versions only if strictly synchronous loading is a hard requirement.