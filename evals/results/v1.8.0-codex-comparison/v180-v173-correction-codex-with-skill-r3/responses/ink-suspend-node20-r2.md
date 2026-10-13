**Node 20 cannot satisfy all those requirements.** The tui-design reference gives these compatibility boundaries:

| Package | Node 20-compatible line | Newest major |
|---|---|---|
| Ink | **6.x** | 8.x requires Node ≥22 and React ≥19.3 |
| chalk | **5.x** | 6.x requires Node ≥22 |
| commander | **14.x** | 15.x requires Node ≥22.12 |

To pin the newest compatible patches exactly:

```sh
npm install --save-exact ink@6 chalk@5 commander@14
```

However, **Ink 6 has no `suspendTerminal` API**. It arrived in **Ink 7.1**, which requires Node ≥22. Inside an Ink component, use:

```tsx
const {suspendTerminal} = useApp();

await suspendTerminal(async () => {
  await runEditor(); // Async subprocess with inherited stdio; await exit.
});
await reloadData();
```

Ink restores terminal modes for the callback and resumes with a full redraw, including on failure. Reload editor-modified data afterward; don’t unmount an app that must resume.

For your full requirement, upgrade to **Node 24 LTS**, then pin:

```sh
npm install --save-exact ink@8 chalk@6 commander@15 react@19.3
```

Node 20 reached end-of-life on April 30, 2026. I couldn’t reach the live npm registry, so these major-version recommendations come from the skill reference; the commands resolve and save exact patch versions.