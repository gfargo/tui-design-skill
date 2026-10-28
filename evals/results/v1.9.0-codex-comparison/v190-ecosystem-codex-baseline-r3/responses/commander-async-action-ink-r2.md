Your action is async, but `program.parse()` doesn’t await async action handlers. That means their rejected promises can become unhandled rejections, and code after `parse()` can run before the action finishes.

Use **`parseAsync()` and await it**, with error handling around the whole operation:

```tsx
program.action(async () => {
  const app = render(<App />);
  await app.waitUntilExit();
});

try {
  await program.parseAsync(process.argv);

  // Runs after the action and waitUntilExit() complete.
  await postRun();
} catch (error) {
  console.error(error);
  process.exitCode = 1;
}
```

If your module doesn’t support top-level `await`, put this in an async `main()` and handle its rejection:

```tsx
async function main() {
  await program.parseAsync(process.argv);
  await postRun();
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
```

Simply switching to `parseAsync()` without awaiting or catching its promise won’t fix the ordering or error handling.