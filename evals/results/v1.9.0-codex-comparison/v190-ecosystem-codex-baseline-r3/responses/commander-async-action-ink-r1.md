Your action is async, but `program.parse()` is synchronous: it doesn’t await the promise returned by the action. That lets post-run code execute early and leaves action rejections unhandled.

Use `parseAsync()` and await it:

```tsx
program.action(async () => {
  const app = render(<App />);
  await app.waitUntilExit();
});

try {
  await program.parseAsync(process.argv);
  // Runs after the action finishes successfully.
} catch (error) {
  console.error(error);
  process.exitCode = 1;
}
```

If your environment doesn’t support top-level `await`, put this in an `async function main()` and call `main().catch(...)`.

The `await app.waitUntilExit()` is correct; the missing piece is awaiting Commander’s async parsing at the entry point.