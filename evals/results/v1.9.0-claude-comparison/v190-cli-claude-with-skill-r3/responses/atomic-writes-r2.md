**Write the report to a temp file in the same directory, then atomically rename it over the real path.** If the program is interrupted or crashes, the final path still holds either the old file or the complete new one, never a truncated one.

## The recipe

1. **Create the temp file in the target's directory**, not in `/tmp`. A rename across filesystems fails or turns into a non-atomic copy. Give it a name you can recognize, like `.report.json.XXXX.tmp`.
2. **Write everything, flush, then `fsync` the file.** The flush empties your buffers. The `fsync` makes sure the data is on disk before the rename. Without it, a power loss can leave a correctly named file that is empty.
3. **Set the final permissions yourself.** `mkstemp`-style temp files are created as `0600`. Use `0644`, or copy the mode of the existing target if one exists. Don't rely on umask.
4. **Rename the temp file over the target.** On POSIX, `rename` is atomic, so readers see the old file or the new one and nothing in between.
5. **`fsync` the directory** (POSIX) if the new directory entry itself needs to survive a power cut.
6. **On any failure or Ctrl+C, delete the temp file and exit non-zero.** Never leave a partial result at the final path.

## Python

```python
import os, tempfile

def write_atomic(path, data: bytes, mode=0o644):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=f".{os.path.basename(path)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)          # os.replace, not os.rename (Windows)
        dfd = os.open(d, os.O_RDONLY)  # POSIX only
        try: os.fsync(dfd)
        finally: os.close(dfd)
    except BaseException:              # includes KeyboardInterrupt
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise                          # let Ctrl+C propagate; don't sys.exit(130)
```

## Go

```go
func writeAtomic(path string, data []byte, mode os.FileMode) (err error) {
	dir := filepath.Dir(path)
	f, err := os.CreateTemp(dir, "."+filepath.Base(path)+".*.tmp")
	if err != nil { return err }
	defer func() {
		if err != nil { os.Remove(f.Name()) }
	}()
	if _, err = f.Write(data); err != nil { f.Close(); return err }
	if err = f.Sync(); err != nil { f.Close(); return err }
	if err = f.Close(); err != nil { return err }
	if err = os.Chmod(f.Name(), mode); err != nil { return err }
	if err = os.Rename(f.Name(), path); err != nil { return err }
	if d, derr := os.Open(dir); derr == nil { d.Sync(); d.Close() }
	return nil
}
```

Libraries that do this for you: `github.com/google/renameio` (Go), `tempfile::NamedTempFile::persist` or the `atomic-write-file` crate (Rust), and `write-file-atomic` (Node).

## Ctrl+C and crashes

- **Ctrl+C:** let the interrupt unwind through the cleanup above. If you install a SIGINT handler, delete the temp file, restore the default handler and re-raise SIGINT. Don't call `exit(130)`: a shell loop or script only stops when the child actually died of SIGINT. A second Ctrl+C should force an immediate exit.
- **Crash or `kill -9`:** no cleanup runs, but the target is still intact. At worst a `.report.json.*.tmp` file is left behind. That's why the name should be recognizable: you can delete stale ones on the next run.
- **Report it honestly.** If the report didn't finish, print a message on stderr (for example, `report not written: interrupted`) and exit non-zero.

## Caveats

- **Windows:** the replace is best effort, not guaranteed atomic. In Python, use `os.replace`. Go's `os.Rename` isn't atomic there either. The pattern still prevents truncated files in practice.
- **Symlinks and hard links:** renaming over a symlink replaces the link itself, not the file it points to, and breaks hard links. If users might symlink the report path, resolve the link first and write next to the real file.
- **Very large or streamed reports:** if you can't hold the whole report in memory, the pattern still works: stream into the temp file and rename at the end. If a partial report is useful, write it under an explicit name like `report.json.part` (optionally behind a `--partial` flag), say so on stderr, and still exit non-zero.

## How to test it

- Kill the process mid-write with SIGINT and with SIGKILL. Assert that the target is either unchanged or complete, that it parses, and that no temp file remains after SIGINT.
- Assert the exit code: death by signal after Ctrl+C, and non-zero after a write error. Also check that the final file mode is what you expect.

If you tell me the language and show how the report is written now, I can make the change in your code.
