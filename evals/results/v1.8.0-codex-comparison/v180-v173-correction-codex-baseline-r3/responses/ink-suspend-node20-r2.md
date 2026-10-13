**You can’t combine Node 20 with the newest releases and Ink’s built-in editor suspension API.**

As of October 13, 2026:

| Package | Newest compatible with Node 20 | Newest overall | Latest requires |
|---|---:|---:|---|
| Ink | **6.8.0** | **8.0.0** | Node ≥22, React ≥19.3 |
| chalk | **5.6.2** | **6.0.1** | Node ≥22 |
| commander | **14.0.3** | **15.0.0** | Node ≥22.12.0 |

Sources: [Ink releases](https://github.com/vadimdemedes/ink/releases), [chalk releases](https://github.com/chalk/chalk/releases), [commander releases](https://github.com/tj/commander.js/releases).

If Node 20 is fixed, pin:

```json
{
  "ink": "6.8.0",
  "chalk": "5.6.2",
  "commander": "14.0.3"
}
```

**`useApp().suspendTerminal()` arrived in Ink 7.1.0**, so it isn’t available in that Node 20 stack. To get the API and newest packages, upgrade to **Node ≥22.12.0**, then pin `ink@8.0.0`, `chalk@6.0.1`, and `commander@15.0.0`, with React ≥19.3. [API introduction](https://github.com/vadimdemedes/ink/releases/tag/v7.1.0)

Inside an Ink component:

```js
const {suspendTerminal} = useApp();

await suspendTerminal(async () => {
  await runEditor(); // Child uses stdio: 'inherit'; await its exit.
});
```

Ink restores terminal state and redraws when the callback settles, including on errors. [API docs](https://github.com/vadimdemedes/ink#suspendterminalcallback)