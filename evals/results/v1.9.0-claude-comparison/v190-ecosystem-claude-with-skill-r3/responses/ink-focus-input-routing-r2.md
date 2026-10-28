The cause is that `useFocus` only tracks which component Tab has selected. It doesn't stop any keyboard handler from running.

## Why it happens

- **Ink's `useInput` runs for every key in every mounted component** unless you pass `isActive: false`. Your list's handler sees each key you type in the search box, so `j`/`k`, letters, or arrows move the selection.
- **`@inkjs/ui`'s `<TextInput>` doesn't connect to `useFocus` at all.** It listens to every key unless you set `isDisabled`. Pressing ←/→ in the list moves the input's cursor, and letters you press there get typed into the query.

So `isFocused` changes when you press Tab, but nothing reads it, and both handlers keep running.

## The fix: turn each handler off when its component isn't focused

```tsx
import React, {useState} from 'react';
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

const SearchBox = ({onChange}: {onChange: (q: string) => void}) => {
  const {isFocused} = useFocus({id: 'search'});
  return (
    <Box borderStyle={isFocused ? 'bold' : 'single'} paddingX={1}>
      <Text>{isFocused ? '› ' : '  '}</Text>
      {/* TextInput ignores useFocus, so disable it explicitly */}
      <TextInput placeholder="Search…" onChange={onChange} isDisabled={!isFocused} />
    </Box>
  );
};

const FileList = ({files}: {files: string[]}) => {
  const {isFocused} = useFocus({id: 'list', autoFocus: true});
  const [selected, setSelected] = useState(0);

  useInput((input, key) => {
    if (key.downArrow || input === 'j') setSelected(i => Math.min(files.length - 1, i + 1));
    if (key.upArrow || input === 'k') setSelected(i => Math.max(0, i - 1));
  }, {isActive: isFocused}); // only runs while the list has focus

  return (
    <Box flexDirection="column" borderStyle={isFocused ? 'bold' : 'single'}>
      {files.map((f, i) => (
        <Text key={f} inverse={isFocused && i === selected} dimColor={!isFocused && i === selected}>
          {i === selected ? '› ' : '  '}{f}
        </Text>
      ))}
    </Box>
  );
};

export const App = ({allFiles}: {allFiles: string[]}) => {
  const [query, setQuery] = useState('');
  const files = allFiles.filter(f => f.toLowerCase().includes(query.toLowerCase()));
  return (
    <Box flexDirection="column">
      <SearchBox onChange={setQuery} />
      <FileList files={files} />
    </Box>
  );
};
```

What the fix comes down to:
- On the list, use **`useInput(..., {isActive: isFocused})`**.
- On the search box, use **`<TextInput isDisabled={!isFocused}>`**.
- If you have a global `useInput` (for example `q` to quit), turn it off while the search box is focused. Otherwise typing "q" into the search quits the app.

## Related suggestions

- **Keep the query in the parent through `onChange`.** `TextInput` is uncontrolled and has no `value` prop, so you can't set its text directly. To clear it, remount it with a new `key`.
- **Add `/` to jump to search and Esc to go back to the list**, using `useFocusManager().focus('search')` / `focus('list')`. Put the `/` check in the list's handler, which only runs while the list is focused, so typing `/` in the search box still inserts the character.
- **Don't show focus with color alone.** The example uses a bold vs. single border plus the `›` marker, so you can still tell which component has focus under `NO_COLOR`. It also shows the list selection dimmed instead of inverse-video when the list isn't focused.
- **If the list can hold thousands of files, only render the visible slice** (`files.slice(top, top + height)`). Ink still lays out and draws every mounted row, even ones clipped out of view.
