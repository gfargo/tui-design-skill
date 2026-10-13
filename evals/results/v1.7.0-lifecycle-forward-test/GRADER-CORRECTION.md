# Grader correction

`grades.json` in this bundle records `grader.kind: "human"`, but the grading was done by a Codex agent session; the grader name ("Primary Codex release reviewer") refers to that session. The maintainer confirmed this on 2026-10-12. The recorded artifacts are immutable under the evidence policy, so they keep the original value; read the grader kind as `agent`.

The scores themselves are unaffected: each boolean was graded directly against the ordered rubric assertions, and the bundle still validates with `scripts/validate-evidence.sh`.
