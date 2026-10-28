**Use an atomic write: write the report to a temp file next to the target, then rename it over the target.** A rename within one filesystem swaps in the new file all at once. Readers, Ctrl+C and crashes then see either the old report or the complete new one, never half of one.

The truncated file appears because the CLI opens the final path for writing, which empties it straight away, then fills it in over time. Any interrupt during that window leaves the partial file at the real path.

## The recipe

1. **Create the temp file in the same directory as the target**, not in `/tmp`. A rename across filesystems fails, or turns into a copy that isn't atomic. Give it a recognizable name like `.report.json.tmp-XXXX`.
2. **Write all the content** to the temp file.
3. **`fsync` the temp file**, so the data is on disk before the name points to it.
4. **Set the final permissions.** Temp files are created as `0600`, so `chmod` to what users expect (often `0644`). Don't rely on umask.
5. **Close it, then rename it over the target.**
6. **`fsync` the directory** (POSIX only), so the rename itself survives a power loss.
7. **On any failure or interrupt, delete the temp file**, print to stderr that no report was written, and exit non-zero.

### Python

```python
import os, tempfile

def write_atomic(path: str, data: bytes, mode: int = 0o644) -> None:
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=f".{os.path.basename(path)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)          # os.replace, not os.rename (Windows)
    except BaseException:              # includes KeyboardInterrupt
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise                          # let Ctrl+C propagate; don't sys.exit(130)
    if os.name == "posix":
        dfd = os.open(d, os.O_RDONLY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
```

### Go

```go
func writeAtomic(path string, data []byte, perm os.FileMode) (err error) {
	dir := filepath.Dir(path)
	f, err := os.CreateTemp(dir, "."+filepath.Base(path)+".*.tmp")
	if err != nil {
		return err
	}
	tmp := f.Name()
	defer func() {
		if err != nil {
			f.Close()
			os.Remove(tmp)
		}
	}()
	if _, err = f.Write(data); err != nil {
		return err
	}
	if err = f.Sync(); err != nil {
		return err
	}
	if err = f.Chmod(perm); err != nil {
		return err
	}
	if err = f.Close(); err != nil {
		return err
	}
	if err = os.Rename(tmp, path); err != nil {
		return err
	}
	if d, derr := os.Open(dir); derr == nil {
		d.Sync()
		d.Close()
	}
	return nil
}
```

In Rust, the `tempfile` crate's `NamedTempFile::new_in(dir)` followed by `.persist(path)` does the same thing. In Node, the `write-file-atomic` package handles it.

## Ctrl+C specifics

- With temp-then-rename, an interrupt before the rename leaves the old report untouched. Your only remaining job is to remove the temp file.
- **Python:** the `except BaseException: … raise` above handles it. Let `KeyboardInterrupt` propagate.
- **Go:** `defer` does **not** run when SIGINT kills the process. If the write can take a while, use `signal.NotifyContext`, check `ctx.Err()` during the write, return so the cleanup runs, then call `signal.Reset(os.Interrupt)` and re-send SIGINT to yourself.
- **Re-raise SIGINT instead of calling `exit(130)`.** Shell scripts and `for` loops stop only if the child process died from the signal. A tool that catches it and exits 130 looks like it handled the interrupt, so the loop keeps going.
- Make a second Ctrl+C force-exit right away.
- `SIGKILL` and power loss can still leave a stray `.report.json.*.tmp`, but never a broken `report.json`. Because the name pattern is recognizable, you can delete old leftovers at startup.

## Related things to check

- **Output redirected with `> report.txt`:** the shell empties that file before your program even starts, and you can't make that atomic. If users depend on the report file, offer `-o/--output PATH` and use the atomic path there. Keep stdout for streaming and piping.
- **Large or streaming reports:** the same pattern works. Stream into the temp file and rename at the end. If you deliberately keep partial output (for resumable work, for example), give it a clear name like `report.json.part`, say so on stderr, and still exit non-zero.
- **Windows:** replacing an existing file is best effort, not guaranteed atomic. Go's `os.Rename` isn't atomic there. Python's `os.replace` is the right call, but it can still fail if another process has the target open.
- **Test it:** start the CLI against an existing `report.json`, send SIGINT partway through the write, then check three things:
  - `report.json` is byte-for-byte the old version;
  - no `.tmp` file is left behind;
  - the process died from the signal, or exited non-zero, with a message on stderr.

  Also run one case that crashes during the write, for example by injecting an error after half the data.

If you tell me the language and how the report is produced now, I can adapt the write path to your code.
