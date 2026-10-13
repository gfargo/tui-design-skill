**No, don't show it right away.** Wait about **200 ms** first. If the work finishes before then, never draw the spinner.

## Why delay

- **Under ~100 ms feels instant.** Most of your runs finish in that window. A spinner that draws and clears in 40 ms just looks like a glitch.
- **Fast runs stay silent.** With a delay, the common case prints only the result. That also keeps output clean for piping and scripts.
- **Set the threshold above your fast path's tail.** If fast runs sometimes take 120 ms, a 100 ms delay will still flash on them. 150–300 ms works well. The slow case takes seconds anyway, so 200 ms of nothing before the spinner appears doesn't matter.

## Frames

Use the common "dots" set (from `cli-spinners`, used by ora and others):

```
⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
```

Advance one frame every **80 ms**. It reads as a smooth clockwise rotation, and all ten frames are the same width.

If you want something heavier, this one also works:
```
⣾ ⣽ ⣻ ⢿ ⡿ ⣟ ⣯ ⣷
```

## Details that matter more than the frames

1. **Write to stderr**, never stdout, so `cmd | jq` still works.
2. **Only animate if stderr is a TTY.** Skip it when `CI` is set or `TERM=dumb`.
3. **Fall back to ASCII** (`| / - \`) if the locale isn't UTF-8. Braille glyphs show up as boxes in some fonts and on older Windows consoles.
4. **Clear it completely** when done: `\r\x1b[2K`. If you hide the cursor (`\x1b[?25l`), restore it (`\x1b[?25h`) on every exit path, including SIGINT and panics.
5. **Optional: keep it visible for at least ~300 ms** once it appears. This stops a run that ends at 210 ms from flashing for one frame. It matters less in a CLI than in a GUI.
6. **Add a label** if the slow case has a clear cause, e.g. `⠹ Fetching index…`. That tells the user why this run is slow.

## Sketch

```
start = now()
done  = run_work_async()
if wait(done, 200ms): print result; exit      # fast path: no spinner
if isatty(stderr): spinner.start("Working…")
wait(done)
spinner.clear()
print result
```
