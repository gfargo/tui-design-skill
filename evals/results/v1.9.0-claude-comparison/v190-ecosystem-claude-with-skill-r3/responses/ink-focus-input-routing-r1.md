## Why it happens

`useFocus` only records which component Tab selected. It doesn't stop any other component from receiving keys. In Ink, every mounted `useInput` handler gets every keystroke unless you turn it off with `isActive: false`. So both components are reading the same keys:

- **The list's `useInput`** runs on every key, including the ones you type into the search box. If it handles arrows, `j`/`k`, or letters, typing moves the selection.
- **@inkjs/ui's `<TextInput>`** has its own internal `useInput` and doesn't use Ink's focus system at all. It listens to everything until you pass `isDisabled`. That's why arrow keys and letters pressed "in the list" also edit the search text.

The `isFocused` value from `useFocus` only takes effect where you pass it into these gates yourself.

## The fix: gate each input on its focus

```tsx
import React, {useState} from 'react';
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

const Search = ({onChange}: {onChange: (q: string) => void}) => {
  const {isFocused} = useFocus({id: 'search'});
  return (
    <Box>
      <Text bold={isFocused}>{isFocused ? '▸ ' : '  '}/ </Text>
      {/* TextInput ignores useFocus: mute it explicitly */}
      <TextInput placeholder="filter…" onChange={onChange} isDisabled={!isFocused} />
    </Box>
  );
};

const FileList = ({files}: {files: string[]}) => {
  const {isFocused} = useFocus({id: 'list', autoFocus: true});
  const [selected, setSelected] = useState(0);

  useInput((input, key) => {
    if (key.downArrow || input === 'j') setSelected(i => Math.min(files.length - 1, i + 1));
    if (key.upArrow || input === 'k') setSelected(i => Math.max(0, i - 1));
  }, {isActive: isFocused}); // without this, the list hears every key typed into search

  return (
    <Box flexDirection="column">
      {files.map((f, i) => (
        <Text key={f} wrap="truncate-end" inverse={isFocused && i === selected}>{f}</Text>
      ))}
    </Box>
  );
};
```

The rule: **every `useInput` gets `{isActive: isFocused}`, and every @inkjs/ui input gets `isDisabled={!isFocused}`.** Any global handler (quit, help, `/` to jump to search) also needs a check so it doesn't fire while the user is typing. For example, `q` should only quit when the search box isn't focused, or the user can't type a "q".

## Related fixes

- **Add a quick way into and out of search.** Bind `/` in the list to `focus('search')` (from `useFocusManager()`), and `Esc` in the search box to `focus('list')`. Tab still works, but these are the keys users expect from fzf, k9s and lazygit.
- **Consider having one focus owner instead of two.** In an fzf-style picker the text box always has focus, and ↑/↓ (plus Ctrl+N/Ctrl+P) move the list from the same `useInput`. Nothing can conflict, and no Tab is needed. Use it if search is the main way people use the list. Keep two focus zones if people mostly browse the list.
- **Clearing the search box:** @inkjs/ui's `TextInput` is uncontrolled and has no `value` prop. To reset it, remount it with a new `key`.
- **Make focus visible without color.** Only the focused pane shows the reverse-video selection, and the search prompt gets a `▸` marker and bold text (as in the code above). That keeps focus clear under `NO_COLOR`.
- **Pasting:** in Ink 7+, `usePaste` delivers a paste as one chunk. Without it, a pasted path arrives one character at a time through any input handler that isn't gated.
