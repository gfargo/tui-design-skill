Not quite. Document it this way:

- Exit code `2`: a common convention for command-line usage or parse errors, but not a universal/BSD standard.
- `EX_USAGE = 64`: the BSD `sysexits.h` usage-error value—a richer legacy vocabulary, but not portable as a standard.

For maximum portability, promise only `0` for success and a documented nonzero failure scheme. If you use `64`, document the numeric value and don’t imply every platform provides `sysexits.h`.
