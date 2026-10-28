Use **atomic file replacement**: write the entire report to a temporary file, then rename it over the destination once it’s complete.

1. Create a uniquely named temp file **in the destination directory** so it’s on the same filesystem.
2. Write the report to the temp file.
3. Flush application buffers. For durability across power loss or an OS crash, also `fsync` the temp file.
4. Close it and atomically rename/replace it over the report.
5. For power-loss durability on POSIX, `fsync` the parent directory after the rename.

```text
temp = create_temp_file(report.parent)
try:
    write_report(temp)
    flush(temp)
    fsync(temp)                 # if crash durability matters
    close(temp)
    atomic_replace(temp.path, report)
    fsync_directory(report.parent)  # POSIX durability
finally:
    remove_temp_if_it_exists()
```

If Ctrl+C or a process crash happens before replacement, the previous report stays intact; afterward, readers see the complete new report. On a first run, interruption may leave no report, but never a partially written destination.

A few details matter:

- **Don’t open the destination with truncation first.** That destroys the old report before the new one is ready.
- Use your platform’s atomic replacement API; avoid deleting the destination before renaming.
- Signal handlers can help clean up temporary files, but correctness must not depend on cleanup running.
- Replacement creates a new file, so set required permissions and other metadata on the temp file before committing.
- Atomic replacement prevents partial files; concurrent writers still need coordination if “last writer wins” is unacceptable.

Filesystem and network-share guarantees vary, so check the guarantees of your target platform.