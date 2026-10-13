**You can’t have both Node 20 compatibility and Ink’s built-in terminal suspension API.** As of October 13, 2026:

| Package | Newest pin for Node 20 | Latest overall | Latest requires |
|---|---:|---:|---|
| Ink | `6.8.0` | `8.0.0` | Node ≥22, React ≥19.3 |
| chalk | `5.6.2` | `6.0.1` | Node ≥22 |
| commander | `14.0.3` | `15.0.0` | Node ≥22.12.0 |

Sources: [Ink manifests](https://github.com/vadimdemedes/ink/blob/v6.8.0/package.json), [Ink latest](https://github.com/vadimdemedes/ink/blob/v8.0.0/package.json), [chalk releases](https://github.com/chalk/chalk/releases), [commander releases](https://github.com/tj/commander.js/releases).

If Node 20 is fixed, pin exactly:

```json
{
  "dependencies": {
    "ink": "6.8.0",
    "chalk": "5.6.2",
    "commander": "14.0.3"
  }
}
```

**For the requested editor API, upgrade to Node ≥22.12.0** and pin `ink@8.0.0`, `chalk@6.0.1`, and `commander@15.0.0`, with React ≥19.3.

The API is **`useApp().suspendTerminal(callback)`**, introduced in Ink **7.1.0**. Await the editor’s completion inside the callback, using inherited stdio; Ink restores the terminal and redraws even if the callback throws. [Introduction](https://github.com/vadimdemedes/ink/releases/tag/v7.1.0), [API documentation](https://github.com/vadimdemedes/ink#suspendterminalcallback).

```tsx
const {suspendTerminal} = useApp();

await suspendTerminal(async () => {
  await runEditor(); // Spawn with stdio: 'inherit'; await child exit.
});
```