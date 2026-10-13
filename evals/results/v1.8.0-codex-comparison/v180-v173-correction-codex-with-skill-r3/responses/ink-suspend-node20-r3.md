**Node 20 cannot support both the newest packages and Ink’s editor handoff API.** The tui-design reference gives these compatible major lines:

| Package | Stay on Node 20 | Current major / requirement |
|---|---|---|
| Ink | **6.x** — React ≥19 | **8.x** — Node ≥22, React ≥19.3 |
| chalk | **5.x** | **6.x** — Node ≥22 |
| commander | **14.x** | **15.x** — Node ≥22.12 |

**`useApp().suspendTerminal()` requires Ink 7.1+.** It is unavailable in Ink 6. To meet all your requirements, upgrade to **Node 24 LTS**, then pin exact releases within Ink 8, chalk 6, and commander 15.

The editor handoff looks like:

```tsx
const {suspendTerminal} = useApp();

await suspendTerminal(async () => {
  await runEditor(); // Await the child’s exit; inherit terminal stdio.
});

await reloadEditedData();
```

Ink restores terminal modes and redraws even if the callback throws. Reloading edited data remains your responsibility; don’t unmount a UI you intend to resume.

Node 20 reached end-of-life on April 30, 2026. I couldn’t verify npm’s latest patch releases because network access failed, so these are compatible major lines, not verified exact patch pins.