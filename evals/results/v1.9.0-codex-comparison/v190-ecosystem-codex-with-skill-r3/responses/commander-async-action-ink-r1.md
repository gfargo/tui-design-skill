The problem is `program.parse()`: it doesn’t await async action handlers. Your `await app.waitUntilExit()` is correct, but the caller must also await Commander’s async parsing.

```tsx
program.action(async () => {
  const app = render(<App />);
  await app.waitUntilExit();
});

try {
  await program.parseAsync();
  // Post-run code belongs here.
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
```

This connects the full promise chain: Ink exit → action completion → parsing completion. Rejections reach the `catch`, and post-run code waits until the UI exits and terminal cleanup finishes.

`await program.parse()` won’t fix it—use `parseAsync()`. Prefer `process.exitCode` over immediate `process.exit()` so pending output can finish.