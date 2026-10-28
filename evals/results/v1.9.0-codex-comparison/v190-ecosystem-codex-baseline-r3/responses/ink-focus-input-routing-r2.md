`useFocus()` tracks **which component is focused**; it doesn’t automatically restrict keyboard input to that component. `useInput()` listeners remain active unless you explicitly gate them.

Gate the list’s handler with `isActive`, and disable the `TextInput` when its wrapper isn’t focused:

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
      onChange={query => {
        // Update search results.
      }}
    />
  );
}
```

The two controls use different switches:

- Ink’s `useInput`: **`isActive: isFocused`**
- `@inkjs/ui`’s `TextInput`: **`isDisabled={!isFocused}`**

Keep both wrappers registered with `useFocus()` so Tab can reach them. Don’t set `useFocus({isActive: isFocused})`: that controls participation in focus navigation and can make an unfocused control unreachable.

Apply the same gating to any other keyboard handlers that should only run while their component is focused.