Use **one fixed footer row**, with frequent actions first and `? help` always last. Assuming these eight actions:

**80 columns**
```text
Enter open | Space mark | / find | c copy | m move | d delete | q quit | ? help
```

**60 columns**
```text
Enter open | Space mark | / find | c copy | m move | ? help
```

**40 columns**
```text
Enter open | / find | q quit | ? help
```

These occupy 79, 59, and 37 cells respectively.

- **On resize:** remove whole hints by priority; never wrap or cut a key from its label. Hidden shortcuts still work, and `?` lists every action.
- **Styling:** bold keys, normal labels, muted separators. Keep the ASCII layout readable without color.
- **Context:** while finding files, replace the row with `Enter apply | Esc cancel`. Help closes with `Esc`. Delete opens a confirmation.
- **Clutter audit:** zero borders, icons, or redundant markers; one row costs 4.2% of an 80×24 screen.

At 60 and 40 columns, give the file list the full width and open previews on demand. Treat 40 columns as the supported minimum; below that, show `Need 40 columns; resize or q to quit`.