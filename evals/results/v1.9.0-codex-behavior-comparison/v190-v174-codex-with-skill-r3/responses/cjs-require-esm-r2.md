**No—you can keep CommonJS without pinning old packages.** The distinction is synchronous ESM versus ESM that uses top-level `await`.

- **Chalk:** On **Node 22.12+**, `require()` can load synchronous ESM. For modern Chalk, use `require('chalk').default`.
- **Ink:** Ink 6.8–8 depends on Yoga’s top-level `await`, so `require('ink')` throws `ERR_REQUIRE_ASYNC_MODULE`. Use dynamic `import()` inside your CommonJS entry point.

```js
// cli.cjs
const chalk = require('chalk').default;
const React = require('react');

async function main() {
  const {render, Text} = await import('ink');

  const app = render(
    React.createElement(Text, null, chalk.green('Ready'))
  );
  await app.waitUntilExit();
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

Set your Node floor to **22.12 or newer**, and satisfy your chosen Ink version’s React peer requirement. If you compile TypeScript, ensure it preserves `import('ink')` rather than rewriting it to `require()`.

If **every dependency must load synchronously through `require()`**, current Ink won’t fit that constraint; keeping CommonJS itself is fine.