Use **one fixed footer row**, with frequent actions first and `? help` always last. Assuming these eight actions:

**80 columns**
```text
 Enter open  Space select  / filter  c copy  m move  d delete  q quit  ? help
```

**60 columns**
```text
 Enter open  Space select  / filter  c copy  q quit  ? help
```

**40 columns**
```text
 Enter open  / filter  q quit  ? help
```

- Hide lower-priority hints as width shrinks; their bindings still work. `?` opens the complete action list.
- Remove whole hints; never wrap or truncate a key/action pair.
- Bold the keys, use normal text for labels, and give the row a subtle background. Keep it readable without color.
- Update hints for the current context: a filter prompt shows `Enter apply  Esc cancel`. Confirm deletion before executing it.

This adds no borders, icons, or repeated markers and uses just **1 of 24 rows** at 80×24. The footer supports 40 columns; below that, retain essential controls and help as space permits.