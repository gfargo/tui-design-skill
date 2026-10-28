`useFocus` only tracks focus. It doesn't route keys anywhere.

## Why it happens

In Ink, every mounted `useInput` handler gets every keypress. `useFocus()` records which component Tab last selected and gives you `isFocused`, but it doesn't mute any other handler. So:

- **The list:** its `useInput` runs on every key, so arrow keys and letters reach it even while the search box has focus.
- **The `@inkjs/ui` `<TextInput>`:** it has its own internal key handler and doesn't connect to Ink's focus system. It reads every key unless you pass `isDisabled`. Calling `useFocus` in the component around it changes nothing for the input.

Both components are listening the whole time, so each key goes to both.

## The fix

Make each handler depend on its own focus state:

- For your own `useInput` handlers, pass `{isActive: isFocused}`.
- For `@inkjs/ui` inputs, pass `isDisabled={!isFocused}`.

```tsx
import React, {useState} from 'react';
import {Box, Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

const SearchBox = ({onChange}: {onChange: (q: string) => void}) => {
  const {isFocused} = useFocus({autoFocus: true});
  return (
    <Box borderStyle="round" borderColor={isFocused ? 'cyan' : 'gray'}>
      <TextInput
        placeholder="Search…"
        onChange={onChange}
        isDisabled={!isFocused}   // ← the actual fix for the input
      />
    </Box>
  );
};

const FileList = ({files}: {files: string[]}) => {
  const {isFocused} = useFocus();
  const [selected, setSelected] = useState(0);

  useInput((_input, key) => {
    if (key.downArrow) setSelected(i => Math.min(files.length - 1, i + 1));
    if (key.upArrow) setSelected(i => Math.max(0, i - 1));
  }, {isActive: isFocused});      // ← the actual fix for the list

  return (
    <Box flexDirection="column">
      {files.map((f, i) => (
        <Text key={f} inverse={isFocused && i === selected} dimColor={!isFocused}>
          {i === selected ? '› ' : '  '}{f}
        </Text>
      ))}
    </Box>
  );
};
```

Tab still switches between the two, because Ink's focus manager handles Tab on its own. The difference is that only the focused component now acts on the other keys.

## Related gotchas

- **Show which pane has focus.** Once input is gated, the user needs to see which pane will get their keys. A border color change or dimming the inactive pane (as above) is enough.
- **Global shortcuts:** if you have an app-wide `useInput` (for example `q` to quit), it will also fire while the user is typing. Typing "query" would then quit the app. Gate it with `isActive: !searchFocused`, or require a modifier key or `Esc` first.
- **Modals and dialogs:** the same rule applies. When a dialog is open, set the list's `isActive` to `false` with a mode flag, or the list will keep moving behind the dialog.
- **Clearing the search:** `@inkjs/ui` `TextInput` is uncontrolled and has no `value` prop. To reset it, remount it with a new `key`.
- **Optional extra:** a common pattern is to let Down/Enter in the search box move focus to the list with `useFocusManager().focus('list')`, so users don't need Tab for the usual flow.
