The directory is empty (no `package.json` or `.nvmrc`), so this answer is based on what I know as of mid-2026, not on your project.

## Versions

- **Ink 6.x**: This is the current major line as far as I know. Ink 6 dropped support for older runtimes and React versions.
- **React 19**: Ink 6 requires React ≥19 as a peer dependency. Pin `react` to 19.x. You don't need `react-dom`.
- **Node 20+**: Ink 6 requires Node ≥20. I'd target **Node 22 LTS** (or 24 if your users have it). Node 20 reached end-of-life in April 2026, so don't make it your floor for a new project.
- **ESM only**: Ink is ESM-only, so set `"type": "module"` in `package.json`.

It's now October 2026, past what I know for certain, and a newer Ink major may have shipped since. Run this before you pin anything:

```sh
npm view ink version engines peerDependencies
```

## `useStdout().stdout.columns`

Yes, that still works. `stdout` is the Node `WriteStream` that Ink renders to, usually `process.stdout`. Two catches:

1. **It doesn't update on resize.** Reading `columns` during render gives you the width at that moment, and nothing triggers a re-render when the terminal is resized.
2. **It can be `undefined`.** When output isn't a TTY (piped, CI, some test setups), `columns` is unset. Always provide a fallback.

A small hook covers both:

```tsx
import {useEffect, useState} from 'react';
import {useStdout} from 'ink';

export function useTerminalWidth(fallback = 80) {
	const {stdout} = useStdout();
	const [width, setWidth] = useState(stdout.columns ?? fallback);

	useEffect(() => {
		const onResize = () => setWidth(stdout.columns ?? fallback);
		stdout.on('resize', onResize);
		return () => {
			stdout.off('resize', onResize);
		};
	}, [stdout, fallback]);

	return width;
}
```

Newer Ink releases may include a built-in hook for terminal dimensions, so check the README for the version you install. If there is one, use it instead of the custom hook.

I can also scaffold the project: `package.json` with engines and peer deps, `tsconfig`, an entry point, and a test setup with `ink-testing-library`.
