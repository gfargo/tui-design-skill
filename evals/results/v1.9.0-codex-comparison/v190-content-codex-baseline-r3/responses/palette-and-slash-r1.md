Yes—35 actions across several screens is enough to justify a command palette, especially for occasional actions and commands whose shortcuts are hard to remember. Keep frequent actions directly accessible.

Use `/` to **search logs in the current view**. That matches terminal conventions and the main job of a log viewer.

A useful split:

| Input | Behavior |
|---|---|
| `/` | Open log search, scoped to the current view |
| `n` / `N` | Jump to next / previous match |
| `Esc` | Close search input; preserve the query and highlights |
| `Ctrl+P` | Open the command palette |
| `?` | Show shortcuts and help |

Search should initially **highlight matches and navigate between them**. Give filtering a separate, clearly labeled action because hiding nonmatching lines changes the context users see.

Make the palette searchable by action name and common synonyms, show each action’s shortcut, and prioritize actions available on the current screen. Include navigation such as “Go to sources” alongside commands such as “Export visible logs.” If an action is unavailable, explain why.

When a text field has focus, `/` should type a slash normally.