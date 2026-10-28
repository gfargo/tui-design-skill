Use **atomic replacement**: write the entire report to a temporary file, then rename it over the destination only after writing succeeds. Never open the existing report with truncation enabled.

The sequence is:

1. Create a unique temporary file **in the destination’s directory** so it’s on the same filesystem.
2. Write the complete report.
3. Flush buffered output and close the file, checking for errors.
4. Atomically replace the destination with the temporary file using your platform’s replace operation.
5. Delete the temporary file if anything fails.

If Ctrl+C or a process crash interrupts the write, the previous report stays intact. On the first run, the final path stays absent until the report is ready. A hard kill may leave a temporary file behind, but it won’t expose a partial report at the final path.

If you also need protection against **power loss or an OS crash**, add durability steps: `fsync` the temporary file before replacement, then `fsync` the containing directory afterward where supported. Atomic replacement prevents partial visibility; syncing helps ensure the completed update survives a reboot.

A few caveats:

- Use a proper platform replacement API; deleting the old file before renaming creates a gap.
- Replacement creates a new file, so preserve or explicitly set permissions as needed.
- Concurrent writers need coordination if “last successful writer wins” is unacceptable.
- Network filesystems may provide different guarantees.

Signal handlers can help clean up temporary files, but correctness should come from the write-and-replace sequence—cleanup handlers don’t run after every kind of crash.