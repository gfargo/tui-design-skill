`useFocus` tracks focus; it **doesn’t route or suppress keyboard events**. Every active `useInput` listener receives keys, regardless of which component has focus.

You need to gate both controls:

- Your list’s `useInput`: `{isActive: isFocused}`.
- `@inkjs/ui`’s `TextInput`: `isDisabled={!isFocused}`. It doesn’t integrate with `useFocus` automatically.

```tsx
import React, {useState} from 'react';
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

function FileList({files}: {files: string[]}) {
  const {isFocused} = useFocus({id: 'files', autoFocus: true});
  const [selected, setSelected] = useState(0);

  useInput((input, key) => {
    if (files.length === 0) return;

    if (key.downArrow || input === 'j') {
      setSelected(i => Math.min(i + 1, files.length - 1));
    }
    if (key.upArrow || input === 'k') {
      setSelected(i => Math.max(i - 1, 0));
    }
  }, {isActive: isFocused});

  return (
    <Box flexDirection="column">
      <Text>{isFocused ? '> Files' : '  Files'}</Text>
      {files.map((file, i) => (
        <Text key={file} inverse={i === selected}>
          {file}
        </Text>
      ))}
    </Box>
  );
}

function SearchBox({onChange}: {onChange: (query: string) => void}) {
  const {isFocused} = useFocus({id: 'search'});

  return (
    <Box>
      <Text>{isFocused ? '> Search: ' : '  Search: '}</Text>
      <TextInput
        isDisabled={!isFocused}
        onChange={onChange}
        placeholder="Filter files..."
      />
    </Box>
  );
}
```

Keep Ink’s built-in Tab/Shift+Tab focus switching; no extra Tab handler is needed. Also gate any app-wide printable shortcuts such as `q`, `/`, or `j/k` while search owns input.

`TextInput` is uncontrolled: use `onChange` to update your filter, and `defaultValue` for an initial query—not a `value` prop.

Verify both directions: typing `j` in search changes only the query; after tabbing to the list, arrows move only the selection and leave the query unchanged.