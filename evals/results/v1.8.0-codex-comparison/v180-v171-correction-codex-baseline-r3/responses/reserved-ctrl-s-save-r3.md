Not universally. Many terminals enable **XON/XOFF flow control** by default, which intercepts Ctrl+S and pauses terminal output before your TUI receives it. Ctrl+Q resumes output.

You can safely use Ctrl+S if your TUI disables flow control while running—usually by entering raw mode with `IXON` cleared—and restores the original terminal settings on exit. Check your terminal library’s raw-mode behavior; “raw mode” implementations vary.

Provide an alternate save binding too, for terminals or remote sessions that still intercept Ctrl+S. Vim’s traditional save command is `:w`; Ctrl+S isn’t a universal Vim default.