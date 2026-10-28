**The bug:** with an async action you have to use `parseAsync()`, not `parse()`.

`program.parse()` is synchronous. Commander calls your action, gets a Promise back, and ignores it. That causes both symptoms:

1. **Unhandled rejections.** Nothing awaits or catches the Promise the action returns. If it rejects, nobody handles it, so Node reports an unhandled rejection. Commander's own error handling (`exitOverride`, `configureOutput`, etc.) never sees it.
2. **Post-run code runs too early.** `parse()` returns as soon as the action *starts*. Anything after it runs while Ink is still rendering and before `waitUntilExit()` resolves.

**Fix:**

```tsx
program
  .command('run')
  .action(async () => {
    const app = render(<App />);
    await app.waitUntilExit();
  });

async function main() {
  try {
    await program.parseAsync(process.argv);
    // post-run code goes here; it now runs after Ink exits
  } catch (err) {
    console.error(err instanceof Error ? err.message : err);
    process.exitCode = 1;
  }
}

void main();
```

Or with top-level await in ESM: `await program.parseAsync();`

**Two related Ink points:**

- **Errors inside your React tree** don't reject `waitUntilExit()` on their own. To send a failure back to the action, call `exit(error)` from `useApp()`. `waitUntilExit()` then rejects with that error, and the `try/catch` above catches it:
  ```tsx
  const { exit } = useApp();
  useEffect(() => {
    doWork().then(() => exit(), (e) => exit(e));
  }, []);
  ```
- **Use `process.exitCode = 1` instead of `process.exit(1)`** where you can. That lets Ink restore the terminal (cursor, raw mode) before the process ends.

In short, switch to `await program.parseAsync()` and put the `try/catch` around it, not inside the action.
