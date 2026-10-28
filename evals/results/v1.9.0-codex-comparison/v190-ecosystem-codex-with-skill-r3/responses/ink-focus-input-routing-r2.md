`useFocus` tracks focus; **it does not route or consume keyboard events**. Every active `useInput` listener receives keys, regardless of which component Tab selected.

Gate both sides explicitly:

- Your list: `useInput(handler, {isActive: isFocused})`.
- `@inkjs/ui`’s `TextInput`: `isDisabled={!isFocused}`. It doesn’t integrate with Ink focus automatically.

```tsx
import {useState} from 'react';
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

function FileList({files}: {files: string[]}) {
  const {isFocused} = useFocus({autoFocus: true});
  const [selected, setSelected] = useState(0);

  useInput((input, key) => {
    if (key.downArrow || input === 'j') {
      setSelected(i => Math.min(Math.max(0, files.length - 1), i + 1));
    }
    if (key.upArrow || input === 'k') {
      setSelected(i => Math.max(0, i - 1));
    }
  }, {isActive: isFocused});

  return (
    <Box flexDirection="column">
      <Text bold={isFocused}>
        {isFocused ? '> Files' : '  Files'}
      </Text>
      {files.map((file, i) => (
        <Text key={file} inverse={isFocused && i === selected}>
          {file}
        </Text>
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

Ink handles Tab/Shift+Tab focus cycling. Keep the input mounted so its text survives focus changes; `@inkjs/ui`’s `TextInput` is uncontrolled and uses `defaultValue`, not `value`.

Apply the same gating to other panel shortcuts, especially printable keys such as `j`, `k`, or `q`. If a modal opens, include its state too: `isActive: isFocused && !modalOpen`.

Verify: typing `j` in Search changes only the query; arrows in Files change only selection; Tab and Shift+Tab switch ownership without clearing the query.