**Why:** `useFocus` only *reports* focus. It doesn't route keystrokes. In Ink, every `useInput` hook that is active receives every keypress, whether or not its component has focus. `@inkjs/ui`'s `TextInput` runs its own `useInput` internally, and it doesn't know about your `useFocus` call. So both components handle every key:

- When you type in the search box, your list's `useInput` also sees those keys. Any letter bindings (`j`/`k`, type-to-jump and so on) move the selection.
- When you press arrows in the list, `TextInput` also sees them. Left/right move its cursor, and any other keys you've bound in the list get typed into the search text.

Tab works because Ink's focus manager handles Tab/Shift+Tab itself. That's why it looks like focus is working.

**Fix:** use the `isFocused` value to switch off each component's input handling.

- For your own `useInput`, pass `{isActive: isFocused}`.
- For `@inkjs/ui` components (`TextInput`, `Select` and others), pass `isDisabled={!isFocused}`.

```tsx
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

function SearchBox({onChange}: {onChange: (q: string) => void}) {
  const {isFocused} = useFocus({autoFocus: true});

  return (
    <Box borderStyle="round" borderColor={isFocused ? 'cyan' : 'gray'}>
      <TextInput
        placeholder="Search…"
        onChange={onChange}
        isDisabled={!isFocused}   // stops TextInput's internal useInput
      />
    </Box>
  );
}

function FileList({files}: {files: string[]}) {
  const {isFocused} = useFocus();
  const [index, setIndex] = React.useState(0);

  useInput(
    (input, key) => {
      if (key.upArrow) setIndex(i => Math.max(0, i - 1));
      if (key.downArrow) setIndex(i => Math.min(files.length - 1, i + 1));
    },
    {isActive: isFocused}         // only listen while focused
  );

  return (
    <Box flexDirection="column">
      {files.map((f, i) => (
        <Text key={f} inverse={isFocused && i === index}>{f}</Text>
      ))}
    </Box>
  );
}
```

Things to watch for:

1. **Call `useFocus` in the component that owns the input.** In the example, the `useFocus` call sits in a small wrapper around `TextInput`. That's because `TextInput` doesn't register itself with Ink's focus system.
2. **Every `useInput` needs the guard.** That includes app-level handlers, like one that quits on `q`. Without it, typing `q` in the search box will quit the app. For global shortcuts, either use keys that can't be typed as text (Ctrl-combos, Esc), or check `useFocusManager().activeId` / pass `isActive: !searchFocused`.
3. **Keep the selection in range.** If the search box filters the list, clamp or reset `index` when `files` changes so the highlight doesn't point past the end of the list.
