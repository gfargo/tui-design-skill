# Lifecycle direct-rubric grading protocol v1

For each recorded trial, compare the raw response with the ordered assertions in `evals/v170-lifecycle-evals.json` from the exact source commit recorded in `run.json`.

- Grade every assertion independently as `true` or `false`; do not infer an aggregate result while grading.
- Pass only when the response substantively satisfies the complete assertion. Equivalent wording and code are acceptable.
- Fail an assertion when any required part is omitted, contradicted, or implemented by code that defeats the prose recommendation.
- Ignore presentation style, answer length, and optional details that are outside the assertion.
- Record a concise evidence note for every boolean, then let the harness calculate totals.
