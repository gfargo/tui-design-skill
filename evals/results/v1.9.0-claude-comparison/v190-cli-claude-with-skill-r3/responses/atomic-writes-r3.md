The fix is to never write the report directly to its final path. Write it to a temp file in the same directory, flush and `fsync` it, then rename it over the target. A rename on the same filesystem is atomic, so a reader or a crash sees either the old file or the complete new one, never half of one.

## The procedure

1. **Create the temp file next to the target**, not in `/tmp`. A rename across filesystems fails or turns into a copy, which isn't atomic. A dotfile name like `.report.json.XXXX.tmp` keeps it out of the way.
2. **Write the whole report into the temp file.** Streaming in chunks is fine.
3. **Flush and `fsync` the file.** Without this, a power loss after the rename can leave an empty or zero-filled file at the final path.
4. **Set the final permissions.** Temp files are created with mode `0600`, so `chmod` to what users expect, such as `0644`.
5. **Rename over the target.** In Python use `os.replace`, not `os.rename`. In Go use `os.Rename`.
6. **Optionally, `fsync` the directory.** This makes the rename itself survive a power cut. It only works on POSIX.
7. **On any failure or Ctrl+C, delete the temp file and exit non-zero.** The previous report stays untouched.

## Python

```python
import contextlib, os, tempfile

@contextlib.contextmanager
def atomic_write(path, mode=0o644):
    path = os.path.abspath(path)
    d, name = os.path.split(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=f".{name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yield f                      # caller streams the report here
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)            # the atomic step
    except BaseException:                # includes KeyboardInterrupt
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise                            # let Ctrl+C keep propagating
    if os.name == "posix":
        dfd = os.open(d, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)

with atomic_write("report.json") as f:
    for chunk in build_report():
        f.write(chunk)
```

## Go

```go
func writeAtomic(path string, write func(io.Writer) error) (err error) {
	dir, base := filepath.Split(filepath.Clean(path))
	if dir == "" {
		dir = "."
	}
	tmp, err := os.CreateTemp(dir, "."+base+".*.tmp")
	if err != nil {
		return err
	}
	defer func() {
		if err != nil {
			tmp.Close()
			os.Remove(tmp.Name())
		}
	}()
	if err = write(tmp); err != nil {
		return err
	}
	if err = tmp.Sync(); err != nil {
		return err
	}
	if err = tmp.Close(); err != nil {
		return err
	}
	if err = os.Chmod(tmp.Name(), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}
```

If you use Rust, `tempfile::NamedTempFile::new_in(dir)` followed by `.persist(path)` does the same thing.

## Handling Ctrl+C correctly

- **Don't add a signal handler just to delete the temp file.** In Python, `KeyboardInterrupt` already runs the `except` cleanup shown above. In Go, if the program doesn't call `signal.Notify`, a Ctrl+C kills the process, the rename never happens, and the target is unchanged. The worst case is a leftover `.tmp` file, which is harmless.
- **If you do catch SIGINT,** for example to cancel work and remove the temp file: do the cleanup within a time limit, then **re-raise SIGINT instead of calling `exit(130)`**. This lets a calling shell script or `for` loop see that the process was killed by the signal and stop. In Python, let `KeyboardInterrupt` propagate. In Go, call `signal.Reset(os.Interrupt)` and then `syscall.Kill(os.Getpid(), syscall.SIGINT)`. A second Ctrl+C should force the program to exit.
- **Tell the user what happened** on stderr, for example `interrupted — report.json left unchanged`.

## Edge cases

- **Leftover temp files:** `SIGKILL` or a power cut can leave `.report.json.*.tmp` files behind. The final file is still safe. Optionally, delete old ones on the next run.
- **Resumable partial output:** if a half-finished report is genuinely useful, keep it under an explicit name like `report.json.part`, say so on stderr, and exit non-zero. Never leave it at the final path.
- **Windows:** `os.replace` and `MoveFileEx` replace the target as a best effort, but atomicity isn't guaranteed (Go's `os.Rename` isn't atomic there). The directory `fsync` isn't available.
- **Output to stdout:** if users can pass `-o -`, that output can't be made atomic, because the consumer owns it. A non-zero exit code is your only signal that it's incomplete, so make sure every failure path returns one.
- **Symlinked targets:** a rename replaces the symlink itself, not the file it points to. If that matters, resolve the path with `realpath` first.

## Testing

Write a black-box test that starts the binary with an existing `report.json`, sends it SIGINT partway through the write (a test hook that slows the writer helps), and then checks four things:

- the original file is byte-for-byte unchanged;
- no `.tmp` files are left;
- the process died from SIGINT, or exited non-zero on Windows;
- stderr contains the "unchanged" message.

Add a second case where the writer raises an error partway through.
