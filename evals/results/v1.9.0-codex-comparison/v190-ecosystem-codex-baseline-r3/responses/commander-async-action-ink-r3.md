Your action is async, but `program.parse()` does **not await async action handlers**. That lets post-run code execute early and leaves rejected action promises unhandled.

Use `parseAsync()` and await it:

```tsx
program.action(async () => {
  const app = render(<App />);
  await app.waitUntilExit();
});

async function main() {
  await program.parseAsync(process.argv);

  // Runs after the action finishes.
  console.log('Done');
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

If you use ESM with top-level await, you can instead wrap `await program.parseAsync(process.argv)` in `try/catch`.

This catches errors that reject the action’s promise. Errors in detached callbacks or background tasks still need their own handling.