Use **atomic replacement**: build the report in a temporary file, then publish it in one operation. Never open the final report with truncation.

For a one-shot CLI, the sequence is:

1. Securely create a unique temporary file **in the destination directory**, so it’s on the same filesystem.
2. Write the complete report. Check every write and flush error.
3. Set the intended permissions, then `fsync` the temporary file and close it, checking errors.
4. Atomically replace the destination with the temporary file using the platform’s supported replacement operation. **Don’t delete the old report first.**
5. On POSIX, `fsync` the parent directory to make the replacement durable across power loss.

On filesystems that support atomic replacement, readers see either the previous complete report or the new complete report. Before publication, a crash can leave a temporary file, but cannot truncate the existing report.

Handle Ctrl+C as cancellation: stop generating, perform bounded cleanup, and remove your temporary file if possible. On POSIX, restore the default SIGINT handler and re-raise SIGINT after cleanup; a second Ctrl+C should force termination. **Correctness must survive without cleanup**—SIGKILL and crashes can bypass it.

Keep the CLI contract honest:

- Print success only after publication and required durability steps succeed.
- Send progress and errors to stderr; incomplete work must not exit successfully.
- If retaining partial results is useful, use an explicit `.part` filename and report its location.
- Prefer `tool --output report.json` for this guarantee. With `tool > report.json`, the shell truncates the destination before your program starts.

Use a platform-aware implementation: Windows replacement and durability guarantees differ, and network filesystems need separate verification.

Test by interrupting or killing the process during writing and around replacement, and inject disk-full and permission errors. The final path should always contain the old complete report, the new complete report, or remain absent if none existed.