**No—you can keep your CLI CommonJS without pinning old dependencies.** CommonJS can load ESM packages using dynamic `import()`:

```js
// cli.cjs
async function main() {
  const {default: chalk} = await import('chalk');
  const {render, Text} = await import('ink');
  const React = require('react');

  render(React.createElement(Text, null, chalk.green('Hello!')));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

If you specifically need **synchronous `require()`**, the details matter:

- **Node 22.12+** supports requiring synchronous ESM by default; **22.13+** removes the default experimental warning.
- **Chalk 5** can use `const chalk = require('chalk').default` on those versions.
- **Ink needs more care:** if its dependency graph uses top-level `await`—as Yoga-based versions can—`require()` throws `ERR_REQUIRE_ASYNC_MODULE`. Use `import()` for that graph.

I’d keep CommonJS, use dynamic imports at startup, and choose Chalk/Ink versions according to their Node engine requirements. Pinning older releases is only necessary if synchronous loading is a hard requirement.