`program.parse()` is synchronous. Commander calls your async action, gets a Promise back, and doesn't await it. So:

- **Post-run code runs too early.** Anything after `program.parse()` runs as soon as the action hits its first `await` (`app.waitUntilExit()`), while the Ink app is still on screen.
- **Errors become unhandled rejections.** When the action's Promise rejects (from your own code, or because `waitUntilExit()` rejects after Ink's `exit(err)`), nothing is awaiting it, so Node reports an unhandled rejection.

The fix is to use `parseAsync` and await it:

```tsx
program
  .command('run')
  .action(async () => {
    const app = render(<App />);
    await app.waitUntilExit(); // rejects if the app calls exit(error)
  });

try {
  await program.parseAsync(process.argv);
  // post-run code here now runs after the Ink app exits
} catch (err) {
  console.error(err instanceof Error ? err.message : err);
  process.exitCode = 1;
}
```

Notes:

- **No top-level await (CJS build)?** Use the same pattern without it: `program.parseAsync().then(...).catch(...)`.
- **Setting the exit code:** `process.exitCode = 1` is better than `process.exit(1)`. It lets Ink restore the terminal (cursor, raw mode) and flush output before the process ends.
- **Commander's own errors:** if you use `program.exitOverride()`, Commander's errors (unknown option, missing argument, etc.) also come through as rejections from `parseAsync`. Check `err.code` (for example `'commander.helpDisplayed'`) so you don't print an error after `--help`.
- **Hooks:** if you have `preAction`/`postAction` hooks that are async, they're only awaited under `parseAsync` too.
