**No—you can keep your CLI CommonJS without pinning Chalk 4 or an old Ink.** The distinction is whether the ESM dependency uses top-level `await`.

- **Chalk:** On **Node 22.12+**, `require()` can load synchronous ESM. Access Chalk’s default export:
  ```js
  const chalk = require('chalk').default;
  console.log(chalk.green('Ready'));
  ```

- **Ink:** Ink 6.8–8 loads Yoga, which uses top-level `await`. Consequently, `require('ink')` throws `ERR_REQUIRE_ASYNC_MODULE`. Use dynamic import inside your CommonJS entry point:
  ```js
  const React = require('react');

  async function main() {
    const {render, Text} = await import('ink');
    const app = render(React.createElement(Text, null, 'Ready'));
    await app.waitUntilExit();
  }

  main().catch(error => {
    console.error(error);
    process.exitCode = 1;
  });
  ```

Set your runtime floor to **Node ≥22.12**, and match Ink’s React peer requirement (Ink 8 requires React ≥19.3). If you compile TypeScript, preserve native `import()` rather than transforming it into `require()`.

You only need legacy pins if **every dependency must load synchronously through `require()`**.