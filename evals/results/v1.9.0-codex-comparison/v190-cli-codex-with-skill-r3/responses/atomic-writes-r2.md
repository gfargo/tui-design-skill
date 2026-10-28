Use **write-to-temp, then atomic replace**. Never open the final report path for writing: opening it can truncate the previous report immediately.

For a one-shot CLI, the save sequence should be:

1. Create a unique temporary file **in the report’s directory**, using exclusive creation.
2. Write the complete report, checking all write errors.
3. Flush buffered output, set the intended permissions, then `fsync` the temporary file and close it, checking errors.
4. Atomically replace the destination with the temporary file.
5. On POSIX, `fsync` the parent directory to make the replacement durable.

The same directory matters because a cross-filesystem rename cannot provide this commit step. On filesystems supporting atomic replacement, readers see either the previous complete report or the new complete report. If no previous report exists, the final path stays absent until commit.

**Ctrl+C cleanup is helpful, but safety must survive without it.** On cancellation before commit, remove the temporary file when possible and report cancellation on stderr. A crash or SIGKILL may leave an orphaned temp file; it must never leave partial content at the final path. On POSIX, if you intercept SIGINT, bound cleanup and then restore and re-raise the signal; let a second Ctrl+C force termination.

A few details matter:

- Announce success only after the commit and required durability operations succeed.
- If directory syncing fails after replacement, report that the report was replaced but durability could not be confirmed.
- If partial reports are useful, retain them under an explicit `.part` name, identify that path on stderr, and exit nonzero.
- Use a platform-aware replacement API on Windows; replacement and durability guarantees vary.
- Offer `--output report.txt`: shell redirection such as `tool > report.txt` truncates the destination before your CLI starts.

Test interruption during writing, disk-full/write failures, and replacement failure. The invariant is: **the final report is always complete; incomplete work stays elsewhere.**