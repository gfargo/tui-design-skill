Use **atomic replacement**: build the report in a temporary file, then publish it only when complete. Never open the final report with truncation.

For a one-shot CLI, the write sequence should be:

1. Securely create a unique temporary file **in the destination directory**, ensuring it’s on the same filesystem.
2. Write the entire report, checking all write errors.
3. Flush application buffers, set the intended permissions, `fsync` the file, and check close errors.
4. Atomically replace the destination using the platform’s supported replacement operation.
5. On POSIX, `fsync` the parent directory to make the rename durable across power loss.

Before replacement, an existing report stays intact. After replacement, readers see the complete new report. If no report existed, failure before replacement leaves the final path absent.

Handle cancellation as cleanup: stop work, best-effort remove the temporary file, and report cancellation on **stderr**. On POSIX, preserve SIGINT termination semantics after bounded cleanup; a second Ctrl+C should force exit. **Safety must not depend on cleanup running**—crashes and SIGKILL can leave a temporary file, but must never publish it.

If partial reports are useful, retain them under an explicit `.part` name, identify that path on stderr, and exit nonzero. Announce success only after publication and required durability steps succeed.

Two caveats:

- Atomic replacement and power-loss durability are separate guarantees; Windows and network filesystems need platform-specific handling.
- `tool > report.txt` lets the shell truncate the file before your CLI starts. Provide `tool --output report.txt` for safe file publication.

Test interruptions during writing and around replacement, plus disk-full and permission failures. Assert that the final path always contains either the old complete report or the new complete report.