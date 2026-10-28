`program.parse()` is synchronous: it doesn’t await your async action. That explains both the unhandled rejection and the early post-run code.

Use **`await program.parseAsync()`**, with error handling at the entry point:

```tsx
program.action(async () => {
  const app = render(<App />);
  await app.waitUntilExit();
});

try {
  await program.parseAsync();
  // Post-run work goes here, after the action and Ink finish.
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
```

Your `await app.waitUntilExit()` is correct; the missing await is at the Commander boundary. Even `await program.parse()` won’t fix it—use `parseAsync()`.

Setting `process.exitCode` lets Node finish cleanup and pending output without an abrupt `process.exit()`.