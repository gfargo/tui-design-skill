Use a **single fixed footer row**: frequent actions first, `? help` always last. Assuming these eight bindings:

**80 columns**
```text
Enter open | Space select | / filter | c copy | m move | d delete | q quit | ? help
```

**60 columns**
```text
Enter open | Space select | / filter | q quit | ? help
```

**40 columns**
```text
Enter open | / filter | q quit | ? help
```

Hide lower-priority hints as width shrinks; their shortcuts still work, and `?` opens the complete list. Never wrap or cut a key–label pair. Measure terminal cells when fitting translated labels.

Bold the keys, use normal text for actions and muted separators. Keep the bar borderless: zero border nesting, no icons or redundant markers, and only one row of chrome—1 of 24 rows at 80×24.

Make hints contextual: while filtering, show `Enter apply | Esc cancel`. Keep feedback such as “Copied 3 files” above the footer so help stays visible. The 40-column version is the compact target; below that, retain `? help` as space permits.