## Why it happens

`useFocus` doesn't route input. It only tracks which component is focused and gives you an `isFocused` boolean. Ink sends every keystroke to every active `useInput` handler in the tree, focused or not. So:

- Your list's `useInput` runs on every key, including letters you type into the search box.
- `@inkjs/ui`'s `TextInput` has its own internal `useInput`. It doesn't know about Ink's focus system at all, so it reacts to every key unless you disable it. It ignores up/down and Tab, but left/right move its cursor, and any letters you press while in the list get typed into it.

Tab switching works because Ink's focus manager handles Tab itself. Nothing else is gated by focus.

## The fix

Connect each component's input handling to its own `isFocused`:

- For your own `useInput`, pass `{isActive: isFocused}`.
- For `TextInput`, pass `isDisabled={!isFocused}`. You can't call `useFocus` inside `TextInput`, so wrap it in a small component that does.

```tsx
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

function SearchBox({onChange}: {onChange: (q: string) => void}) {
	const {isFocused} = useFocus({id: 'search', autoFocus: true});

	return (
		<Box borderStyle="round" borderColor={isFocused ? 'cyan' : 'gray'}>
			<TextInput
				placeholder="Search…"
				isDisabled={!isFocused}
				onChange={onChange}
			/>
		</Box>
	);
}

function FileList({files}: {files: string[]}) {
	const {isFocused} = useFocus({id: 'list'});
	const [index, setIndex] = useState(0);

	useInput(
		(input, key) => {
			if (key.upArrow) setIndex(i => Math.max(0, i - 1));
			if (key.downArrow) setIndex(i => Math.min(files.length - 1, i + 1));
			if (key.return) {
				/* open files[index] */
			}
		},
		{isActive: isFocused}, // only listen while the list has focus
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

## Related gotchas

- **Global shortcuts:** if a parent has a `useInput` for keys like `q` to quit or `/` to jump to search, it will also fire while you're typing. Check focus there with `useFocusManager()` and focus IDs, or only handle keys like Ctrl+… or Escape that can't be typed into a search.
- **Jumping focus:** `useFocusManager().focus('search')` moves focus programmatically, for example when the user presses `/` in the list.
- **`TextInput` keeps its own state.** It's uncontrolled, so disabling it keeps the text it already has. To clear or reset it, remount it by changing its `key` (you can set initial text with `defaultValue`).
- **`@inkjs/ui` `Select`/`MultiSelect`:** if you switch the list to one of these, gate it the same way with `isDisabled={!isFocused}`.

The rule: each `useInput` or input component gets `isActive`/`isDisabled` tied to its own `isFocused`.
