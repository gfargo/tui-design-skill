Not universally. Some terminals enable **software flow control**, where Ctrl+S pauses terminal output (XOFF) instead of reaching your TUI. The app can appear frozen; Ctrl+Q resumes output.

Ctrl+S is safe if your TUI’s terminal setup explicitly disables `IXON` while running and restores the original settings on exit. Don’t assume a library’s “raw mode” does this—verify its behavior. Users can also disable it with `stty -ixon`, but that shouldn’t be a prerequisite.

Offer an alternate save binding or command for environments that intercept Ctrl+S before it reaches your app.

Also, Vim’s default save command is `:w`; Ctrl+S isn’t its standard save binding.