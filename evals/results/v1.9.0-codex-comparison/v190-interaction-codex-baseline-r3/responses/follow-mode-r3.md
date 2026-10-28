Treat auto-scroll as **“follow the tail” mode**, controlled by where the user is reading.

- **Start following.** New logs appear immediately, keeping the newest line visible.
- **Pause when the user scrolls up** using the wheel, arrows, Page Up, or Home. Keep the viewport anchored to the same log content as new entries arrive.
- **Show a quiet status:** `Follow paused · 42 new lines · End to resume`. Update the count without moving the viewport.
- **Resume when the user reaches the bottom**, or explicitly presses End or activates “Follow.”
- **Keep search and text selection stable.** Incoming logs should never move a match or selection out from under the user.

If your buffer drops the lines they’re reading, move to the oldest retained line and show `Older logs expired`.

The core rule: **new output can update the logs, but only the user’s navigation should interrupt their reading.**