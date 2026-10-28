`useFocus()` tracks focus and enables Tab navigation; it **doesn’t route keyboard events**. Each active `useInput()` listener still receives input, including the listener inside `TextInput`.

Connect focus to input handling in both components:

```tsx
import {Text, useFocus, useInput} from 'ink';
import {TextInput} from '@inkjs/ui';

function FileList() {
  const {isFocused} = useFocus({autoFocus: true});

  useInput((input, key) => {
    if (key.upArrow) {
      // Move selection up.
    } else if (key.downArrow) {
      // Move selection down.
    }
  }, {isActive: isFocused});

  return <Text color={isFocused ? 'cyan' : undefined}>Files…</Text>;
}

function SearchBox({onSearch}: {onSearch: (value: string) => void}) {
  const {isFocused} = useFocus();

  return (
    <TextInput
      placeholder="Search…"
      isDisabled={!isFocused}
      onChange={onSearch}
    />
  );
}
```

The two connections are:

- **Custom list:** `useInput(handler, {isActive: isFocused})`.
- **`@inkjs/ui` `TextInput`:** `isDisabled={!isFocused}` gates its internal input handler.

Keep both `useFocus()` registrations enabled so Tab can reach both controls. Setting `useFocus({isActive: false})` removes a component from focus navigation; it does not disable that component’s keyboard listeners.