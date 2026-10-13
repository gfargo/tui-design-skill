**Ctrl+S is a reasonable save default for a full-screen editor TUI, provided its terminal setup disables software flow control.** Don’t assume that merely entering the alternate screen or disabling line buffering does this.

On POSIX terminals, `IXON` enables XON/XOFF: Ctrl+S pauses output and Ctrl+Q resumes it. Standard raw mode (`cfmakeraw`) clears `IXON`, allowing your app to receive Ctrl+S. Verify your framework’s actual settings and restore the original terminal state on exit and suspend.

Also:

- Provide another save path, such as `:w` or a command menu. Multiplexers can intercept Ctrl+S—Zellij’s default bindings and GNU Screen with `flow on` are examples.
- Test saving and terminal restoration in a real PTY, including suspend/resume.
- Don’t require users to run `stty -ixon`; manage your app’s terminal mode.

One correction: **Vim and Helix don’t default to Ctrl+S for writing files.** Both support `:w`; Helix’s Ctrl+S saves a selection. Nano and micro are closer precedents for Ctrl+S-to-save.