No, not in Lipgloss v2. `fmt.Println(style.Render(msg))` sends color escapes into pipes and ignores `NO_COLOR`.

**Why:** In v2, `Style.Render` no longer checks the terminal. It always returns full truecolor ANSI. Only Lipgloss's own print functions (`lipgloss.Print*`, `Sprint*`, `Fprint*`) route output through a `colorprofile.Writer`. That writer checks the actual destination and the environment, then reduces or strips the escapes to match. `fmt.Println` skips that step, so:

| Situation | `fmt.Println(style.Render(msg))` | `lipgloss.Println(style.Render(msg))` |
|---|---|---|
| Interactive terminal | Truecolor, even if the terminal can't show it | Reduced to what the terminal supports |
| `mytool \| grep …` or `> out.txt` | Raw `\x1b[38;2;…m` bytes in the file | Plain text |
| `NO_COLOR=1` | Still colored | Colors removed. Bold, underline and similar stay, as no-color.org allows |
| `TERM=dumb` | Still colored | Plain text |

v1 checked the terminal inside `Render`, so this pattern used to work. It's a common thing to miss when upgrading.

**Fix:** use the Lipgloss print functions, and match the function to the stream you're writing to:

```go
lipgloss.Println(okStyle.Render("✓ deployed api"))               // results → stdout
lipgloss.Fprintln(os.Stderr, errStyle.Render("error: no token")) // diagnostics → stderr
```

Use `Fprintln(os.Stderr, …)` for stderr, not `Println`. The check runs against the stream you write to. With `mytool | jq`, stdout is a pipe but stderr is still the terminal. Errors should stay colored there while stdout stays plain.

**A `--color=always|never|auto` flag** (recommended for CLIs, with the flag taking priority over environment variables, which take priority over auto-detection): set the profile yourself and write through that writer:

```go
w := colorprofile.NewWriter(os.Stdout, os.Environ()) // github.com/charmbracelet/colorprofile
switch colorFlag {
case "always":
	w.Profile = colorprofile.TrueColor
case "never":
	w.Profile = colorprofile.NoTTY
}
fmt.Fprintln(w, style.Render(msg)) // fine here: w does the downsampling
```

`fmt.Fprintln` is fine in this case because the writer does the work. I haven't run this snippet, so check the `colorprofile` API against the version you depend on.

**Other things to check:**
- **Meaning without color:** in plain mode only the text is left. Write "✓ deployed" or "error: …" rather than relying on green or red alone. Borders and padding still print as characters, so make sure a piped result still parses easily, or skip the decoration when output isn't a terminal.
- **Machine output:** if scripts read your output, offer `--json` or another stable plain format rather than relying on color stripping alone.
- **Tests:** test the built binary with no terminal attached and with `NO_COLOR=1`. Check stdout, stderr and the exit code, and keep golden files as plain text. Colored goldens break when CI runs with different `TERM` or `COLORTERM` values.
