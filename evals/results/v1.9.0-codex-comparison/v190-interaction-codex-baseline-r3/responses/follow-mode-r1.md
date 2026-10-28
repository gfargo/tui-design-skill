Use **“follow the tail” as an explicit state**, rather than scrolling whenever a log arrives.

- **Start following.** New lines keep the viewport at the bottom.
- **Pause when the user scrolls up.** Keep the text they’re reading anchored as logs arrive.
- **Show a quiet indicator:** `Follow paused · 42 new lines · End to resume`. Count lines received while paused.
- **Resume when they reach the bottom**, or press an explicit shortcut such as `End`. Clear the unread count.
- **Keep search and text selection stable.** Incoming logs shouldn’t move the viewport or steal focus.

If your log buffer is bounded, preserve the visible position by line ID. If those lines are evicted, show a small notice such as `Older lines expired` and anchor to the oldest remaining line.

The core rule: **new output can move the viewport only while the user is following.**