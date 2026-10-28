Write the report to a temporary file and **atomically rename** it over the real path once it's complete. Readers then see either the old file or the finished new one, never a partial one. (The working directory is empty, so I can't see your code. These are general patterns.)

## The pattern

1. **Create the temp file in the same directory** as the target, e.g. `report.json.tmp-<random>`. It has to be on the same filesystem, or `rename` isn't atomic and may fail.
2. **Write the full contents** to the temp file.
3. **Flush and `fsync`** the file so the data is on disk before the rename. Without this, a power loss can leave a renamed but empty file.
4. **`rename(tmp, final)`**. On POSIX this atomically replaces the target.
5. Optionally, **`fsync` the directory** so the rename itself survives a power loss.
6. **On any error or interrupt, delete the temp file** and leave the original untouched.

Ctrl+C and crashes then just leave behind a stray `.tmp` file at worst, never a truncated report.

## Python

```python
import os, tempfile

def write_atomic(path, data: bytes):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=os.path.basename(path) + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)          # atomic on POSIX and Windows
        dfd = os.open(d, os.O_RDONLY)  # persist the rename (POSIX)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    except BaseException:              # includes KeyboardInterrupt
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
```

## Node.js

```js
import { open, rename, unlink } from "node:fs/promises";
import { dirname, basename, join } from "node:path";
import { randomBytes } from "node:crypto";

export async function writeAtomic(path, data) {
  const tmp = join(dirname(path), `.${basename(path)}.${randomBytes(6).toString("hex")}.tmp`);
  const fh = await open(tmp, "w");
  try {
    await fh.writeFile(data);
    await fh.sync();
    await fh.close();
    await rename(tmp, path);
  } catch (e) {
    await fh.close().catch(() => {});
    await unlink(tmp).catch(() => {});
    throw e;
  }
}
```
Off-the-shelf options: the `write-file-atomic` npm package; `atomicwrites` in Python (archived, but fine as a reference); `github.com/google/renameio` in Go; `tempfile::NamedTempFile::persist` in Rust.

## Points that often get missed

- **Build the report first, write it last.** If you currently stream output into the final file as you compute, either buffer it in memory or stream into the temp file. Either way, only the final `rename` makes it visible.
- **Signals:** a default SIGINT kills the process before cleanup runs, but your original file is still safe. To clean up temp files on Ctrl+C, catch SIGINT/SIGTERM, delete the temp file, and exit with code 130. Python's `KeyboardInterrupt` already goes through the `except` above. `SIGKILL` and power loss can't be caught; the worst case there is an orphaned `.tmp` file.
- **Orphaned temp files:** give them a recognisable prefix or suffix so you can delete old ones on the next run if you want.
- **Permissions:** `mkstemp` creates files with mode `0600`. If the report should match the old file's mode, `chmod` the temp file before renaming.
- **Windows:** `os.replace` and Node's `rename` overwrite the target, but they can fail if another process has it open. Retry briefly if that matters for your users.
- **Symlinks:** if the target path is a symlink, `rename` replaces the link itself rather than the file it points to. Resolve it first if that matters.
- **Writing to stdout or a pipe** can't be made atomic. If users redirect output (`> report.txt`), the shell truncates the file before your program runs. Offer an `--output FILE` flag that uses the atomic write.

If you tell me which language your CLI uses or point me at the write code, I can adapt this to it directly.
