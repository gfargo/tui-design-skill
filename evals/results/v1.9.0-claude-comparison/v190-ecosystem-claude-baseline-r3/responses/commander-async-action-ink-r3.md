The problem is that you're calling `program.parse()` with an async action handler.

## What's wrong

In Commander, `.parse()` is synchronous. It calls your action handler, gets a Promise back, and ignores it. That causes both of your symptoms:

1. **Unhandled rejections:** if the action throws, or `waitUntilExit()` rejects (for example when a component calls `exit(new Error(...))` from `useApp()`), nothing is awaiting that Promise. Node reports it as an unhandled rejection.
2. **Code running too early:** `parse()` returns as soon as the action hits its first `await`. Anything after `program.parse()` runs while the Ink app is still mounted.

## Fix

Use `parseAsync()` and await it. It returns a Promise that settles only after your async action has finished.

```tsx
#!/usr/bin/env node
import { Command } from 'commander';
import { render } from 'ink';
import { App } from './App.js';

const program = new Command();

program
  .name('mycli')
  .action(async () => {
    const app = render(<App />);
    await app.waitUntilExit(); // rejects if the app calls exit(error)
  });

async function main() {
  try {
    await program.parseAsync(process.argv);
    // post-run code here now runs only after the Ink app has exited
  } catch (err) {
    console.error(err instanceof Error ? err.message : err);
    process.exitCode = 1;
  }
}

main();
```

If your package is ESM with top-level await, you can write `await program.parseAsync()` directly at the bottom of the file, still inside a `try/catch`.

## Related points

- **Every subcommand needs this too.** If any subcommand has an async action, the root must use `parseAsync`. Commander chains the action Promises, but only `parseAsync` hands that chain back to you.
- **Prefer `process.exitCode = 1` over `process.exit(1)`.** This lets Ink restore the terminal (cursor, raw mode) and flush output before Node exits on its own.
- **Commander's own errors** (unknown option, missing argument) call `process.exit` directly by default, so they won't reach your `catch`. If you want to handle them yourself, add `program.exitOverride()`. Those errors are then thrown as `CommanderError` and land in the same `catch`.
- **Errors inside React rendering** don't reject `waitUntilExit()` on their own. To get them into that Promise, catch them (with an error boundary, or try/catch in effects) and call `exit(err)` from `useApp()`.
