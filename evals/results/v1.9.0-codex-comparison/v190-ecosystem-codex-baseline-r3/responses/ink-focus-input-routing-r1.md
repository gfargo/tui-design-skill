`useFocus()` tracks which component is focused, but **doesn’t route keyboard events**. Every active `useInput()` handler still receives input, including the handler inside `TextInput`.

Connect focus to each component’s input handling:

```tsx
import {useFocus, useInput} from 'ink';
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

  return /* your list */;
}

function SearchBox() {
  const {isFocused} = useFocus();

  return (
    <TextInput
      isDisabled={!isFocused}
      placeholder="Search…"
      onChange={query => {
        // Update search.
      }}
    />
  );
}
```

The two controls serve different purposes:

- `useFocus({isActive})` controls participation in Tab navigation.
- `useInput(..., {isActive})` controls whether a keyboard handler runs.
- `TextInput`’s `isDisabled` controls its internal input handler.

Keep both components registered with `useFocus`, and gate their keyboard handling with `isFocused`. Ink continues handling Tab and Shift+Tab to switch focus. Returning early from one handler doesn’t consume the event or stop another handler from receiving it.