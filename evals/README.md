# Evaluation evidence contract

`scripts/eval_harness.py` is the authoritative semantic validator for recorded runs. The JSON Schemas under `evals/schema/` are stable, machine-readable structural anchors for external tooling; once published, a schema version is immutable. A behavioral change that makes an existing valid artifact invalid requires a new version.

## Schema versions

- **v4** is the current format. Run, grade, and summary artifacts declare their canonical schema URI. New runs are always v4.
- **v3** and **v2** are accepted so historical evidence can still be validated from its recorded source snapshot.

Schema v3 adds caller-reported runner and generation provenance. Executed runs require an exact runner version. Seed and temperature are recorded when exposed. A system prompt is represented as one of `recorded`, `none`, or `unavailable`; `recorded` stores only the SHA-256 digest and byte length, never the prompt or its path.

Schema v4 adds `grading_prompt` to grades: a `{path, sha256}` object that machine-links `grader.prompt_sha256` to a grading-prompt file preserved inside the same evidence bundle. `path` is relative to the directory containing the grades document; the harness resolves it, rejects any path that is absolute or escapes that directory, and requires the file to exist with a SHA-256 that matches both `grading_prompt.sha256` and `grader.prompt_sha256`. Before schema v4, that relationship could only be checked by running `sha256sum` by hand. v2 and v3 grades never had this field and continue to validate under their original rules — `grading_prompt` is not retrofitted onto them.

### Immutability policy

Once a schema version is published, its rules never change. A behavioral change that would make an existing valid artifact invalid — a newly required field, a stricter check, a renamed property — always ships as a new schema version (its own `evals/schema/vN/` directory and a bump to the harness's `SCHEMA_VERSION` and `SUPPORTED_SCHEMA_VERSIONS`), never as an edit to a published version's files or validation rules. Fixing a mistake in a past release does not mean rewriting or reinterpreting that release's committed evidence: historical run/grades/summary bundles keep the schema version, hashes, and meaning they were recorded with, validated only against their own recorded source snapshot (see the run checklist below), not against whatever the referenced skill or eval-set files contain today.

The harness cannot prove that an arbitrary runner honored caller-reported settings. Evidence reviewers should compare the run manifest with the runner command or provider record. Exact runner arguments remain private by default because they may contain credentials or signed URLs.

## Run checklist

1. Use an immutable eval-set commit and a clean skill tree.
2. Record the exact provider, model, and runner version.
3. Record exposed seed and temperature values. Use `--system-prompt-file` to hash a known prompt, `--no-system-prompt` only when there truly is none, or omit both when the provider does not expose it.
4. Keep credentials in the runner environment. Use `--record-runner-argv` only after checking every argument for secrets.
5. Preserve prompts, responses, stderr, `run.json`, `grades.json`, `summary.json`, and (schema v4) the grading-prompt file named by `grading_prompt.path` together in the run directory.
6. Validate all three artifacts with `--require-completed` before committing evidence.

The validator compares eval-set and skill hashes with the checked-out files. To revalidate historical evidence after those inputs have changed, first check out the clean commit recorded in `run.json`; accepting an older schema does not substitute newer files for the original inputs.

Example:

```bash
python3 scripts/eval_harness.py run \
  --eval-set evals/v161-correction-evals.json \
  --condition with-skill \
  --provider openai \
  --model exact-model-id \
  --runner-version "runner 1.2.3" \
  --temperature 0 \
  --system-prompt-file /path/to/system-prompt.txt \
  --repeat 2 \
  -- path/to/model-runner --its-arguments
```

For schema-v3+ grades, `grader.prompt_version` names the grading protocol and `grader.prompt_sha256` anchors its exact instructions. A model grader also records its provider, model, runner version, and generation metadata. Human grading uses `kind: "human"` and does not invent model fields. Schema-v4 grades additionally require `grading_prompt: {"path": "grading-prompt.md", "sha256": "<same digest as grader.prompt_sha256>"}`, naming the committed file that carries those exact instructions.

Validation with a summary intentionally requires the corresponding grades so the harness can recompute totals and per-case results instead of trusting aggregate fields:

```bash
python3 scripts/eval_harness.py validate \
  --run evals/runs/RUN_ID/run.json \
  --grades evals/runs/RUN_ID/grades.json \
  --summary evals/runs/RUN_ID/summary.json \
  --require-completed
```
