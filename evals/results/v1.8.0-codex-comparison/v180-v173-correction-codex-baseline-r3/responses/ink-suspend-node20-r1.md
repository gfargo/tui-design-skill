**Node 20 cannot satisfy all those requirements.** As of October 13, 2026:

| Package | Newest release | Minimum Node | Pin for Node 20 |
|---|---:|---:|---:|
| Ink | `8.0.0` | 22 | `6.8.0` |
| chalk | `6.0.1` | 22 | `5.6.2` |
| commander | `15.0.0` | 22.12.0 | `14.0.3` |

These runtime requirements come from the packages’ manifests and documentation. citeturn157106view0turn157106view1turn795850view0turn795850view2turn948886search1turn795850view1

For Node 20, use exact pins:

```json
{
  "dependencies": {
    "ink": "6.8.0",
    "chalk": "5.6.2",
    "commander": "14.0.3"
  }
}
```

**The catch:** `useApp().suspendTerminal()` was introduced in Ink `7.1.0`, which requires Node 22. Ink `6.8.0` does not provide it. citeturn157106search1turn795850view3

To get the newest packages and editor handoff, upgrade to **Node ≥22.12.0**, pin `ink@8.0.0`, `chalk@6.0.1`, and `commander@15.0.0`, and satisfy Ink’s **React ≥19.3.0** peer requirement. Then, inside a component:

```js
const {suspendTerminal} = useApp();

await suspendTerminal(async () => {
  await runEditor(); // Child uses inherited stdio; await its exit.
});
```

Ink restores terminal state and redraws when the callback settles, including when it throws. citeturn157106view0turn948886search0