The working directory is empty, so I couldn't look at your CLI. The general fix works in any language: **never write directly to the final path.** Write to a temporary file, then atomically rename it over the target. If you get interrupted, the user keeps either the old report or the complete new one. They never see a half-written file.

## The pattern

1. Create a temp file **in the same directory** as the target, for example `.report.json.tmp-<pid>-<random>`. It has to be on the same filesystem, because a rename across filesystems isn't atomic and usually fails. That's why you shouldn't use `/tmp`.
2. Write all the content to it.
3. Flush, then `fsync` the file so the data is actually on disk before the rename.
4. `rename(tmp, target)`. This is atomic on POSIX. On Windows, use a replace-style rename, such as `os.replace` or `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING`.
5. Optionally, `fsync` the parent directory so the rename itself survives a power loss.
6. If anything fails, including Ctrl+C, delete the temp file and don't rename.

### Python
```python
import os, tempfile

def write_atomic(path, data: bytes):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=f".{os.path.basename(path)}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)          # atomic, also works on Windows
        dfd = os.open(d, os.O_RDONLY)  # optional: persist the rename (POSIX)
        try: os.fsync(dfd)
        finally: os.close(dfd)
    except BaseException:              # includes KeyboardInterrupt
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
```

### Node.js
```js
import fs from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

export async function writeAtomic(target, data) {
  const tmp = path.join(path.dirname(target),
    `.${path.basename(target)}.${process.pid}.${crypto.randomBytes(4).toString("hex")}.tmp`);
  const fh = await fs.open(tmp, "w");
  try {
    await fh.writeFile(data);
    await fh.sync();
    await fh.close();
    await fs.rename(tmp, target);
  } catch (err) {
    await fh.close().catch(() => {});
    await fs.rm(tmp, { force: true });
    throw err;
  }
}
```
You can also use the existing `write-file-atomic` npm package. In other languages: Go has `github.com/google/renameio`, and Rust has `tempfile::NamedTempFile::persist`.

## Ctrl+C and crashes

- **Ctrl+C (SIGINT/SIGTERM):** let it abort the write and run the cleanup path above. Don't rename on interrupt. In Node, a `process.on("SIGINT")` handler that deletes any temp files you're tracking, then exits with code 130, works well.
- **SIGKILL, crashes, power loss:** no cleanup code runs, so a stray `.report.*.tmp` file may be left behind. The real report is still intact. Give temp files a recognizable name and optionally delete old ones on the next run.
- **Streaming large reports:** the same approach works. Stream into the temp file, then fsync and rename at the end.

## Gotchas

- **Permissions:** the temp file gets default permissions (`mkstemp` uses `0600`). If the existing report has a different mode, copy it over with `chmod` before renaming.
- **Symlinks:** if the target is a symlink, the rename replaces the link itself rather than writing through it. Resolve it with `realpath` first if that matters.
- **Windows:** the rename can fail if another process has the target open, for example an editor or antivirus. Retry a few times with a short backoff.
- **Writing to stdout or a pipe:** you can't make that atomic. If the report can go to stdout, accept the limitation, or buffer the whole report and write it in one go at the end.

If you tell me what language your CLI is in or point me at the code, I can apply this to your actual write path.
