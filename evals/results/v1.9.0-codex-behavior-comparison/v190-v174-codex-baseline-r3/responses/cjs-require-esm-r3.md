No—you can keep your CLI CommonJS without pinning old dependencies. The distinction is whether loading must stay synchronous.

- **Chalk 5:** On Node **22.12+**, `require()` can load synchronous ESM. Use its default export:
  ```js
  const chalk = require('chalk').default;
  ```
- **Modern Ink:** Synchronous `require()` depends on the exact version’s dependency graph. If Ink or a dependency uses top-level `await`, Node throws `ERR_REQUIRE_ASYNC_MODULE`.

Dynamic `import()` works from CommonJS and handles both cases:

```js
// cli.cjs
async function main() {
  const {default: chalk} = await import('chalk');
  const {render, Text} = await import('ink');
  const React = require('react');

  render(React.createElement(Text, null, chalk.green('Ready')));
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

I’d keep CommonJS and use an async entry point. If you require synchronous loading throughout, check the exact Ink version and set a minimum Node **minor** version—“Node 22” alone isn’t precise enough.