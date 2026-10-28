The problem is the `program.parse()` call at the bottom. Your action is fine.

**Why it happens:** Commander's `parse()` is synchronous. It calls your action and ignores the Promise it returns. So:

1. **Unhandled rejection:** Nothing awaits the action's Promise. If it rejects (an error thrown in the action, or `waitUntilExit()` rejecting because the app called `exit(err)`), nothing catches it and Node reports an unhandled rejection.
2. **Code runs too early:** `parse()` returns as soon as the action reaches its first `await`. Any code after `program.parse()` runs while Ink is still rendering, not after the app exits.

**Fix:** Use `parseAsync()` and await it. It waits for async actions to finish and passes their errors back to you.

```tsx
program
  .command('run')
  .action(async () => {
    const app = render(<App />);
    await app.waitUntilExit(); // rejects if the app calls exit(err)
  });

try {
  await program.parseAsync(); // ESM top-level await
  // post-run code here now runs after Ink exits
} catch (err) {
  console.error(err instanceof Error ? err.message : err);
  process.exitCode = 1;
}
```

If you're on CommonJS, or can't use top-level await:

```ts
program.parseAsync().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
```

Notes:
- Keep `await app.waitUntilExit()` inside the action. Without it, the action finishes as soon as Ink mounts, and you'd have the same "runs too early" problem one level down.
- To make the CLI fail from inside the UI, call `useApp().exit(new Error('...'))`. That error rejects `waitUntilExit()`, travels up through `parseAsync()`, and ends up in your `catch`.
- Set `process.exitCode` rather than calling `process.exit()`. That lets Ink restore the terminal (cursor, raw mode) before the process ends.

This matches the tui-design skill's guidance in `references/ecosystem-typescript.md:359`: with any async action, use `await program.parseAsync()`, and await `waitUntilExit()` inside Ink actions.
