Not universally. Many terminals enable **XON/XOFF software flow control** by default, where Ctrl+S pauses terminal output and Ctrl+Q resumes it. Your TUI may never receive Ctrl+S, making it appear frozen.

Ctrl+S is a reasonable save binding if your TUI disables `IXON` while running—often handled by the terminal library’s raw mode—and restores the original terminal settings on exit. Verify your library does this; “raw mode” implementations vary. Keep an alternative save command available.

Also, Vim and Helix normally save with `:w`; Ctrl+S isn’t their standard save binding.