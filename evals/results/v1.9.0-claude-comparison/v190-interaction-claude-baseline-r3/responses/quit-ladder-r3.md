Treat the three keys as three different levels of escape: **Esc goes back one layer, q quits the app, and Ctrl+C always gets you out.**

## Esc: undo the innermost thing, one layer per press

Each press removes exactly one layer, starting with the most temporary state:

1. **Close an overlay.** Popups, menus, help, confirm dialogs, autocomplete.
2. **Cancel editing.** Leave the text input or edit mode and throw away the uncommitted change.
3. **Clear the search or filter.** The full list comes back.
4. **Clear the selection** or multi-select marks.
5. **Go back one level** in the view hierarchy.
6. **At the root, do nothing.** At most, show a hint like "press q to quit".

Rules that keep this predictable:
- **One layer per press.** Never collapse two layers at once. If someone mashes Esc, they should land at the root and stop there.
- **Esc never quits.** People press it repeatedly out of reflex, and it shouldn't cost them their session.
- **Build it as a stack.** Each mode pushes a handler and Esc pops the top one. Then Esc's behaviour comes from the structure instead of a chain of special cases.
- **Show what Esc will do** in the footer, e.g. `esc close filter` or `esc back to Projects`. With five meanings, this matters more than anything else on this list.

## q: quit, except when it's being typed

- **In a text input, q is just the letter q.** This is the most common bug with "q quits from anywhere". Any search box, rename field or command line has to take q as text.
- **Everywhere else, q quits the whole app.** It doesn't mean "back", because that's Esc's job. Two keys that both sometimes go back get confusing quickly.
- **Ask first if there's unsaved work or a task running.** For example: "Quit? 2 unsaved changes [y/N]". Otherwise quit immediately.
- **Optional:** if you want a "close this pane" key in the style of lazygit or less, use a different key or make it `Q` vs `q`. Don't overload q.

## Ctrl+C: always works

- **It works everywhere,** including inside modals, text inputs and confirm dialogs. No layer may swallow it.
- **First press cancels whatever is running,** such as a fetch, a long operation or a pending prompt.
- **If nothing is running, it exits.** If there's unsaved state, show "Press Ctrl+C again to quit" for about a second, and quit on the second press. Don't open a y/N dialog, because a dialog would trap it.
- **Restore the terminal on every exit path.** Leave the alt screen, show the cursor, reset raw mode. Also handle SIGINT and SIGTERM, not just the keypress.

## How they rank

| Situation | Esc | q | Ctrl+C |
|---|---|---|---|
| Typing in a field | cancel edit | types "q" | cancel/quit |
| Modal open | close modal | close modal or quit (choose one and stick with it) | cancel/quit |
| Nested view | back one level | quit | quit |
| Root view | no-op + hint | quit | quit |
| Task running | back (task keeps going) | confirm quit | cancel task |

In short: Esc is the gentlest key and can never lose anything, q is a deliberate quit that respects text input and unsaved work, and Ctrl+C is the escape hatch that no part of the app can block.
