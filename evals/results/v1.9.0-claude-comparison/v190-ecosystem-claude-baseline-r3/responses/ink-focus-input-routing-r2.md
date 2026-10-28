## Why it happens

`useFocus` only tracks focus. It tells a component whether it's focused (`isFocused`) and lets Ink's focus manager move focus with Tab/Shift+Tab. It doesn't filter keyboard input.

Every `useInput` hook that's mounted and active gets **every keystroke**, whatever has focus. So:

- Your list's `useInput` handler runs while you type in the search box, and the list selection moves.
- `@inkjs/ui`'s `TextInput` has its own internal `useInput` that's always listening. It also doesn't know about `useFocus`. So when the list has focus, keys still go into the text field. Left/Right move its cursor, and letters get inserted.

Ink doesn't hide input from unfocused components. Each component has to opt out.

## The fix

Turn off each input handler unless its component has focus:

- **Your list:** pass `isActive` to `useInput`.
- **`TextInput`:** pass `isDisabled`. When it's disabled, its internal `useInput` is inactive.

```tsx
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

function SearchBox({onChange}: {onChange: (v: string) => void}) {
	const {isFocused} = useFocus({autoFocus: true});

	return (
		<Box borderStyle="round" borderColor={isFocused ? 'cyan' : 'gray'}>
			<TextInput
				placeholder="Search…"
				onChange={onChange}
				isDisabled={!isFocused}
			/>
		</Box>
	);
}

function FileList({files}: {files: string[]}) {
	const {isFocused} = useFocus();
	const [index, setIndex] = useState(0);

	useInput(
		(input, key) => {
			if (key.upArrow) setIndex(i => Math.max(0, i - 1));
			if (key.downArrow) setIndex(i => Math.min(files.length - 1, i + 1));
		},
		{isActive: isFocused},
	);

	return (
		<Box flexDirection="column">
			{files.map((f, i) => (
				<Text key={f} inverse={isFocused && i === index}>
					{f}
				</Text>
			))}
		</Box>
	);
}
```

Notes:

- **Keep `useFocus` and `useInput` in the same component.** `TextInput` doesn't call `useFocus` itself, so wrap it in a component like `SearchBox` above. That wrapper owns the focus state and passes it down as `isDisabled`.
- **Tab still works.** `TextInput` ignores Tab, so Ink's focus manager still receives it. Also, a disabled `TextInput` keeps its value.
- **Global shortcuts** (like `q` to quit or Esc) should go in a `useInput` near the top of the app, with no `isActive` gate. Check which component has focus before acting on a key, so typing `q` in the search box doesn't quit. You can track focus with `useFocusManager` or lift `isFocused` into the parent.
