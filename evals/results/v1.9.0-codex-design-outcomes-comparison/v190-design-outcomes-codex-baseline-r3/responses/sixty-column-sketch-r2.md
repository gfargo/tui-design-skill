The repository and commit panes alone need 68 columns, including borders. At 60, use a single full-width pane, initially showing commits.

Each line below occupies 60 columns, including trailing spaces; there are 24 rows.

```text
 Git browser | repo: api-server | COMMITS                   
+-- Commits: main -----------------------------------------+
| Hash     Message                              Author     |
|----------------------------------------------------------|
|>a81f02c  Fix retry backoff                     Maya        |
| 78cd913  Add request timeout                   Eli         |
| 5b2e490  Test connection recovery              Maya        |
| c310a62  Handle empty response                 Jo          |
| 9dd214b  Update client docs                    Eli         |
| 82e6f10  Remove unused adapter                 Jo          |
| 7a903de  Add health endpoint                   Maya        |
| 692b4f1  Improve error messages                Eli         |
| 55dc804  Cache repository metadata             Jo          |
| 4e08b2a  Fix config precedence                 Maya        |
| 3f19d70  Add pagination                        Eli         |
| 2bba106  Test auth failures                    Jo          |
| 194f8c2  Refresh dependencies                  Maya        |
| 0ea76d3  Initial client implementation         Eli         |
|                                                          |
|                                                          |
| Commit 1 of 128 | 3 files changed                          |
+----------------------------------------------------------+
 [1] Repos  [2] Commits  [3/Enter] Diff                       
 Up/Down: select  PgUp/PgDn: page  q: quit                    
```

- **1** opens the repository list at its fixed 28-column width. Selecting a repository with **Enter** returns to its commits.
- **2** opens commits; **3** or **Enter** on a commit opens its full-width diff. **Esc** returns to the previous view.
- **Up/Down** and **PgUp/PgDn** reach off-screen rows. In the diff, **Left/Right** scroll horizontally. Switching views preserves selection and scroll position.

As the terminal shrinks, keep this single-pane navigation. Shorten labels, then omit optional commit columns; truncate long text with `…`. Fewer rows show fewer entries, with scrolling preserved.

Below **40 columns**, the commit pane cannot meet its minimum. Show a compact “Need 40 columns; current: 39” message instead of squeezing it. Below **6 rows**, show a resize message. Clip that message to fit even a tiny terminal. Restore the previous view and position when space returns.