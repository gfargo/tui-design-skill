`program.parse()` is synchronous: it starts your async action but doesn’t await its promise. That causes both symptoms: rejected actions become unhandled rejections, and code after parsing runs before the UI exits.

Use **`await program.parseAsync()`** and catch errors at the entry point:

```tsx
program.action(async () => {
  const app = render(<App />);
  await app.waitUntilExit();
});

try {
  await program.parseAsync();
  // Post-run code goes here, after the action finishes.
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
```

Your `await app.waitUntilExit()` is correct; the missing await is at the Commander boundary. `await program.parse()` won’t fix it, because `parse()` doesn’t return the action’s promise.

For failures from async work inside `<App />`, catch them there and pass the error to Ink’s `useApp().exit(error)` so `waitUntilExit()` rejects through this same chain.