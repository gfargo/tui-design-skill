Assuming “one-shot CLI” means a command that runs once, prints a result, and exits, Windows support mainly changes the implementation and packaging—not the interaction model.

- **Keep the interface stream-based.** Write results to stdout, diagnostics to stderr, and return meaningful exit codes. Avoid requiring a TTY; support pipes and redirected output.
- **Avoid shell dependencies.** Invoke programs with argument arrays instead of building shell strings. Bash syntax, quoting, glob expansion, and commands like `rm` won’t work consistently in PowerShell or `cmd.exe`.
- **Use platform APIs for paths.** Handle drive letters, UNC paths, spaces, and Windows file restrictions. Use standard libraries for temporary files and configuration directories.
- **Keep terminal features optional.** Detect terminal capabilities before using color or cursor control. Provide plain-text output and a `--no-color` option; test Unicode rendering.
- **Handle cancellation and cleanup explicitly.** Unix signals and Windows console events differ. Windows also commonly prevents deleting or replacing files while handles remain open.
- **Ship a Windows-native entry point.** Provide an `.exe` or an appropriate runtime launcher, with clear installation and PATH instructions.
- **Test on Windows itself.** Include PowerShell, paths containing spaces, redirected output, and non-ASCII input in CI.

For a one-shot command, you can usually skip alternate-screen rendering, raw keyboard input, resize handling, and most terminal-state recovery. That makes Windows support substantially simpler than for a full-screen TUI.