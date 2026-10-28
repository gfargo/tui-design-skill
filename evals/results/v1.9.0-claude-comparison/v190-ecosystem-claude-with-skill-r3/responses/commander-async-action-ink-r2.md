The problem is the last line. `program.parse()` is synchronous. It calls your async action, gets back a promise, and returns without waiting for it. That one cause explains both symptoms:

- **Unhandled rejection:** when the action throws, its promise rejects, but nothing is awaiting that promise, so Node reports it as an unhandled rejection.
- **Post-run code runs too early:** anything after `program.parse()` runs as soon as `parse()` returns. At that point Ink is still rendering and `waitUntilExit()` hasn't resolved yet.

Your action itself is written correctly: awaiting `waitUntilExit()` inside it is the right pattern. You just need to wait for the action from the top level too.

**Fix:** use `parseAsync()` and await it.

```ts
#!/usr/bin/env node
import { program } from 'commander';
import { render } from 'ink';
import { App } from './app.js';

program
  .name('mycli')
  .action(async () => {
    const app = render(<App />);
    await app.waitUntilExit(); // resolves when the app exits, rejects if exit(err) is called
  });

try {
  await program.parseAsync(); // waits for the async action to finish
  // post-run code goes here: it now runs after Ink has exited
} catch (err) {
  console.error(err instanceof Error ? err.message : err);
  process.exitCode = 1;
}
```

Notes:
- Top-level `await` only works in ESM (`"type": "module"` or a `.mts` file). In CommonJS, use `program.parseAsync().catch(err => { ... })` instead.
- If you want an error inside the Ink app to reach that `catch`, call `exit(new Error(...))` from `useApp()`. That makes `waitUntilExit()` reject, which rejects the action, which rejects `parseAsync()`.
- Set `process.exitCode` rather than calling `process.exit()`. That lets Ink restore the terminal (cursor, raw mode) before the process ends.

Rule of thumb: if any action is `async`, use `await program.parseAsync()` and never plain `parse()`.
