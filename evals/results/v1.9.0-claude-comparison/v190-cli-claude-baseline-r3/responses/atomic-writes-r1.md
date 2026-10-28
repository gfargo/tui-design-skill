There's no code in this directory, so here's the general fix. It works in any language.

## Write to a temp file, then rename it into place

Never write directly to the final path. Instead:

1. **Write to a temp file in the same directory**, e.g. `report.json.tmp-<pid>-<random>`. It has to be the same directory (same filesystem) or the rename won't be atomic.
2. **Flush and `fsync`** the temp file so the data is actually on disk.
3. **`rename(tmp, final)`**. On POSIX this is atomic: anyone reading the path sees either the old file or the complete new one, never half of it.
4. **(Optional, for power-loss durability) `fsync` the directory** so the rename itself is saved to disk.
5. **On error or interrupt, delete the temp file.** Don't touch the final path.

If Ctrl+C or a crash happens at any point before step 3, the worst case is a leftover `.tmp` file. The real report is either untouched or fully replaced.

### Node.js
```js
import { open, rename, unlink } from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

export async function writeFileAtomic(dest, data) {
  const dir = path.dirname(dest);
  const tmp = path.join(dir, `.${path.basename(dest)}.${process.pid}.${crypto.randomBytes(4).toString("hex")}.tmp`);
  let fh;
  try {
    fh = await open(tmp, "wx", 0o644);   // wx: fail if it already exists
    await fh.writeFile(data);
    await fh.sync();                      // fsync file
    await fh.close(); fh = null;
    await rename(tmp, dest);              // atomic swap
    const dh = await open(dir, "r");      // fsync dir (POSIX; skip on Windows)
    try { await dh.sync(); } finally { await dh.close(); }
  } catch (err) {
    if (fh) await fh.close().catch(() => {});
    await unlink(tmp).catch(() => {});
    throw err;
  }
}
```
(The `write-file-atomic` npm package does this for you.)

### Python
```python
import os, tempfile

def write_atomic(dest, data: bytes):
    d = os.path.dirname(os.path.abspath(dest))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=f".{os.path.basename(dest)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dest)            # atomic, also works on Windows
        dfd = os.open(d, os.O_RDONLY)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    except BaseException:                # includes KeyboardInterrupt
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
```

### Go
Use `github.com/google/renameio`, or the same pattern by hand: `os.CreateTemp(dir, ...)` → write → `f.Sync()` → `f.Close()` → `os.Rename`.

## Ctrl+C and signal handling
- With the pattern above, an interrupt **can't corrupt the report**. Signal handling is only about tidying up the temp file.
- In Node, adding a `SIGINT` listener replaces the default exit. Clean up, then exit with `process.exit(130)`. Python's `except BaseException` above already catches `KeyboardInterrupt`.
- `SIGKILL`, OOM kills and power loss can't be caught, so temp files can still be left behind. Prefix them with `.` and give them a recognizable pattern so you can clean up stale ones on the next run.

## Other things to watch for
- **Streaming large reports:** stream into the temp file and rename at the end. Don't write the final file bit by bit.
- **Windows:** rename onto an existing file can fail if another process has it open. Use `os.replace` in Python, and retry briefly in Node (`write-file-atomic` handles this).
- **Permissions and symlinks:** the new file gets default permissions and replaces a symlink rather than writing through it. If either matters, copy the original file's mode or resolve the symlink first.
- **Writing to stdout (`> report.txt`):** this pattern can't protect shell redirection. If that's common, add an `--output` flag so your tool controls the write.

If you share the file-writing code from your CLI, I can adapt this to it.
