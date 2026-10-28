Use one rule for each key:

- **Ctrl+C** always works, from anywhere.
- **Esc** backs out exactly one layer.
- **q** quits, except while the user is typing.

## Who sees a key first

```
1. Ctrl+C            → global handler, checked before anything else
2. Focused text input → gets every other key (q types "q", Esc leaves the field)
3. Esc               → the topmost layer on the stack handles it, then stops
4. q                 → global quit (only reached when no input has focus)
```

Ctrl+C goes first so a buggy or stuck layer can never trap the user. Text input goes second because "q quits from anywhere" otherwise breaks the first time someone types "quit" into a search box.

## Esc: innermost and cheapest-to-redo first

Your five uses of Esc almost certainly fit this order. Each press undoes one thing, and it should be the most temporary thing currently active:

1. **Close a popup or autocomplete menu.**
2. **Leave text-edit mode** and keep what was typed.
3. **Clear the active filter or search.** The view stays where it is.
4. **Close the modal or dialog.** If it holds unsaved edits, ask "discard?" instead of closing silently.
5. **Pop one navigation level** (detail → list → parent).

At the root, Esc does nothing, or shows a hint like "press q to quit". It should never quit the app. If it did, pressing Esc a few times to back out would close the program.

The easiest way to get this right is to keep the layers on a real stack (popup, input, filter, modal, screen). Esc goes to the top layer, that layer handles it and returns "consumed". Don't use one big Esc handler full of `if` branches, because those drift out of order over time.

## Ctrl+C: cancel the work first, then quit

1. If an operation is running (fetch, build, long query), cancel it and stay in the app.
2. Otherwise, quit. If quitting would lose unsaved state, ask for confirmation, or show "press Ctrl+C again to quit".
3. A second Ctrl+C within about a second always quits, with no prompt. This is the guaranteed way out.

Always restore the terminal on exit (alt screen, cursor, raw mode), including when the app panics.

## q

- q quits from any screen as long as no text field has focus.
- Use the same unsaved-work confirmation as Ctrl+C.
- Don't make q mean "back" on some screens and "quit" on others. Back is Esc's job. Mixing the two is the classic way nested TUIs end up confusing people.

## Show what Esc will do

Five meanings for one key is fine as long as the user can see which one is active. Put the current meaning in the footer and update it live: `esc close menu`, then `esc clear filter`, then `esc back to list`. Because the stack already knows its top layer, that layer can provide this label.
