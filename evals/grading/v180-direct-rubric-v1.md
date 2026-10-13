# Direct rubric grading (v180-direct-rubric-v1)

You grade one answer to a terminal-UI design or engineering question against a numbered list of rubric assertions. You do not know which model wrote the answer or whether it had access to any reference material, and that must not affect your judgment.

For each assertion, decide whether the answer satisfies it:

- Mark it `true` only when the answer clearly makes the point, recommends the behavior, or contains the code the assertion describes. Equivalent wording counts; the exact phrasing does not matter.
- Mark it `false` when the answer omits the point, states it vaguely enough that a reader could miss it, or contradicts it.
- An assertion phrased as "does NOT …" is `true` when the answer avoids the named mistake.
- Judge each assertion independently. Do not reward length, confidence, or formatting.

Reply with a single JSON object and nothing else:

{"results": [true, false, ...]}

The array must have exactly one boolean per assertion, in the order given.
