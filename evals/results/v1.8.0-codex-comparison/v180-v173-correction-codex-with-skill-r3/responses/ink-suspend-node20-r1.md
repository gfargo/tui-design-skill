**Node 20 cannot satisfy all those requirements.** The tui-design reference gives these compatible release lines:

| Package | Stay on Node 20 | Newest major |
|---|---|---|
| Ink | **6.x**; React ≥19 | **8.x**; Node ≥22, React ≥19.3 |
| chalk | **5.x** | **6.x**; Node ≥22 |
| commander | **14.x** | **15.x**; Node ≥22.12 |

Ink’s **`useApp().suspendTerminal()` requires Ink 7.1+**, so it is unavailable on the Node-20-compatible Ink 6 line.

For your complete requirements, upgrade to **Node 24 LTS**, then pin exact releases within **Ink 8, chalk 6, commander 15**, with React ≥19.3. The editor handoff is:

```tsx
const {suspendTerminal} = useApp();

await suspendTerminal(async () => {
  await runEditor(); // Async child process with inherited stdio
});
await reloadEditedData();
```

Ink restores terminal modes for the callback and resumes with a full redraw afterward. Reloading edited data remains your responsibility; don’t unmount the app for this handoff.

Node 20 reached EOL on April 30, 2026. I couldn’t access the live npm registry, so these are **release-line recommendations**, not verified latest patch pins.