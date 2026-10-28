**`useFocus` tracks focus; it doesn’t route or consume keyboard events.** Every active `useInput` receives keys, and `@inkjs/ui`’s `TextInput` doesn’t automatically integrate with Ink’s focus system.

Connect focus to input handling on **both** sides:

```tsx
import {useState} from 'react';
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

function FileList({files}: {files: string[]}) {
  const {isFocused} = useFocus({autoFocus: true});
  const [selected, setSelected] = useState(0);

  useInput((_input, key) => {
    if (key.upArrow) {
      setSelected(i => Math.max(0, i - 1));
    }
    if (key.downArrow) {
      setSelected(i => Math.max(0, Math.min(files.length - 1, i + 1)));
    }
  }, {isActive: isFocused});

  return (
    <Box flexDirection="column">
      <Text bold>{isFocused ? '> Files' : '  Files'}</Text>
      {files.map((file, i) => (
        <Text key={file} inverse={i === selected}>{file}</Text>
      ))}
    </Box>
  );
}

function SearchBox({onChange}: {onChange: (query: string) => void}) {
  const {isFocused} = useFocus();

  return (
    <Box>
      <Text>{isFocused ? '> Search: ' : '  Search: '}</Text>
      <TextInput
        isDisabled={!isFocused}
        onChange={onChange}
      />
    </Box>
  );
}
```

The key distinctions:

- `useInput(..., {isActive: isFocused})` gates your list’s handler.
- `<TextInput isDisabled={!isFocused} />` gates the widget’s internal handler.
- `useFocus({isActive: false})` removes a component from focus eligibility; it doesn’t disable its input listeners.

Keep each component’s `useFocus` registration separate so Tab and Shift+Tab can move between them. Gate printable shortcuts such as `j`, `k`, `/`, and `q` too, so they remain text while searching.

Verify by typing `jkq` in search, then tabbing to the list and pressing arrows: only the focused component should react.