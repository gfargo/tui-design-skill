No—you can keep the CLI CommonJS without pinning both packages. The distinction is **synchronous `require()` versus dynamic `import()`**.

- **Chalk 5:** On Node **22.12+**, `require()` can load synchronous ESM. Use `require('chalk').default` because Chalk’s export is a default export. Node 22.13+ also removes the default experimental warning.
- **Modern Ink:** Its dependency graph can include top-level `await`, notably through Yoga. Synchronous `require()` cannot load that graph; it throws `ERR_REQUIRE_ASYNC_MODULE`. Use dynamic `import()` from your CommonJS entry point.

```js
// cli.cjs
async function main() {
  const {default: chalk} = await import('chalk');
  const {render} = await import('ink');

  // Start your CLI here.
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

This works without converting the project to ESM. **Pin older versions only if synchronous loading is a hard requirement.** Also set an explicit Node minor-version floor if you rely on `require(ESM)`; “Node 22” alone includes versions where it requires a flag.