The project directory is empty, so I couldn't check installed versions. This is from what I know as of mid-2026. Run `npm view ink version` and `npm view ink peerDependencies engines` to confirm the current release before you pin anything.

## Versions to target

| | Target | Why |
|---|---|---|
| **Ink** | `^6` (latest 6.x) | Ink 6 is the current major. Ink 5 is the older React 18 line. |
| **React** | `^19` | Ink 6 requires React 19 or newer. Install the matching `react-devtools-core` only if you use it. Don't add `react-dom`. |
| **Node** | `>=22`, develop on 24 | Ink 6 only requires Node 20 or newer, but Node 20 reached end of life in April 2026. Node 24 is the current Active LTS and 22 is in maintenance. Set `"engines": { "node": ">=22" }`. |

Other things to know:
- **Ink is ESM-only.** Set `"type": "module"` in package.json. If you use TypeScript, use `"module": "NodeNext"` and `"jsx": "react-jsx"`.
- Pin `@types/react` to 19 so the types match React.
- Use `ink-testing-library` for tests. Check that its version works with Ink 6.

## Can you still use `useStdout().stdout.columns`?

Yes. `stdout` is still Node's `process.stdout` (or whatever stream you passed to `render`), so `.columns` works. There are two catches:

1. **It doesn't update on resize.** Reading `.columns` gives you the width at that moment. Your component won't re-render when the terminal is resized.
2. **It can be `undefined`.** This happens when output isn't going to a terminal, such as when it's piped or running in CI. Always provide a fallback.

A small hook handles both:

```tsx
import {useEffect, useState} from 'react';
import {useStdout} from 'ink';

export function useTerminalSize() {
	const {stdout} = useStdout();
	const read = () => ({columns: stdout.columns ?? 80, rows: stdout.rows ?? 24});
	const [size, setSize] = useState(read);

	useEffect(() => {
		const onResize = () => setSize(read());
		stdout.on('resize', onResize);
		return () => {
			stdout.off('resize', onResize);
		};
	}, [stdout]);

	return size;
}
```

Recent Ink 6.x releases may include a built-in hook for terminal size. If yours does, use it instead of this one. Check the Ink changelog or `node_modules/ink/build/hooks/` after you install.

If you'd like, I can scaffold the `package.json`, `tsconfig.json`, and a starter `cli.tsx` with these settings.
