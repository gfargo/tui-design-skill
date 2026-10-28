The problem is that you call `program.parse()`. In Commander, `parse()` is synchronous. It starts your async action but doesn't wait for the Promise the action returns. That causes both of your symptoms:

1. **Unhandled rejection:** if the action throws, or if `waitUntilExit()` rejects (Ink rejects it when the app calls `exit(error)`), nothing is awaiting that Promise. Node reports it as an unhandled rejection instead of the error reaching your code.
2. **Post-run code runs too early:** anything after `program.parse()` runs as soon as the action hits its first `await`. That happens while the Ink app is still on screen, not after it exits.

Your `await app.waitUntilExit()` inside the action is correct. It just doesn't help when nothing awaits the action itself.

**Fix:** use `parseAsync()` and await it.

```tsx
program
  .command('run')
  .action(async () => {
    const app = render(<App />);
    await app.waitUntilExit(); // rejects if the app calls exit(err)
  });

try {
  await program.parseAsync(); // waits for the action to finish
  // post-run code goes here; it now runs after Ink has exited
} catch (err) {
  console.error(err instanceof Error ? err.message : err);
  process.exitCode = 1;
}
```

If your entry file can't use top-level `await` (it needs ESM), use this instead:

```ts
program.parseAsync().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
```

Two details:
- Set `process.exitCode` rather than calling `process.exit()` right away. That gives Ink time to restore the terminal (cursor and raw mode) first.
- To make an error inside the UI fail the command, have the component call `useApp().exit(new Error(...))`. `waitUntilExit()` will then reject, and the error reaches your `catch`.

The skill's TypeScript ecosystem reference covers the same rule in `references/ecosystem-typescript.md:359`.
