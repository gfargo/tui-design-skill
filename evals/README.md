# Evaluation evidence contract

`scripts/eval_harness.py` is the authoritative semantic validator for recorded runs. The JSON Schemas under `evals/schema/` are stable, machine-readable structural anchors for external tooling; once published, a schema version is immutable. A behavioral change that makes an existing valid artifact invalid requires a new version.

## Schema versions

- **v5** is the current format. Run, grade, and summary artifacts declare their canonical schema URI. New runs are always v5.
- **v4**, **v3**, and **v2** are accepted so historical evidence can still be validated from its recorded source snapshot.

Schema v3 adds caller-reported runner and generation provenance. Executed runs require an exact runner version. Seed and temperature are recorded when exposed. A system prompt is represented as one of `recorded`, `none`, or `unavailable`; `recorded` stores only the SHA-256 digest and byte length, never the prompt or its path.

Schema v4 adds `grading_prompt` to grades: a `{path, sha256}` object that machine-links `grader.prompt_sha256` to a grading-prompt file preserved inside the same evidence bundle. `path` is relative to the directory containing the grades document; the harness resolves it, rejects any path that is absolute or escapes that directory, and requires the file to exist with a SHA-256 that matches both `grading_prompt.sha256` and `grader.prompt_sha256`. Before schema v4, that relationship could only be checked by running `sha256sum` by hand. v2 and v3 grades never had this field and continue to validate under their original rules — `grading_prompt` is not retrofitted onto them.

Schema v5 adds `skill_invocation_path` to run manifests. A with-skill prompt reads `Use $tui-design at <absolute skill directory> to solve this request:`, and before v5 that absolute path lived only inside the prompt files, so the validator could reconstruct the prompts only from a checkout at the exact same location. v5 records the path verbatim (null for baseline runs, whose prompts embed no path), and the validator rebuilds the prompts from the recorded value instead of from its own location. The path string is checked, not trusted: it must be absolute, must end with the recorded `skill_dir`, and the reconstructed prompt must still match the preserved prompt file and its recorded SHA-256, while the skill's contents remain anchored by `skill_dir` and `skill_sha256`. v2–v4 manifests never had this field and are not retrofitted; see the portable revalidation recipe below.

### Immutability policy

Once a schema version is published, its rules never change. A behavioral change that would make an existing valid artifact invalid — a newly required field, a stricter check, a renamed property — always ships as a new schema version (its own `evals/schema/vN/` directory and a bump to the harness's `SCHEMA_VERSION` and `SUPPORTED_SCHEMA_VERSIONS`), never as an edit to a published version's files or validation rules. Fixing a mistake in a past release does not mean rewriting or reinterpreting that release's committed evidence: historical run/grades/summary bundles keep the schema version, hashes, and meaning they were recorded with, validated only against their own recorded source snapshot (see the run checklist below), not against whatever the referenced skill or eval-set files contain today.

The harness cannot prove that an arbitrary runner honored caller-reported settings. Evidence reviewers should compare the run manifest with the runner command or provider record. Exact runner arguments remain private by default because they may contain credentials or signed URLs.

## Run checklist

1. Use an immutable eval-set commit and a clean skill tree.
2. Record the exact provider, model, and runner version.
3. Record exposed seed and temperature values. Use `--system-prompt-file` to hash a known prompt, `--no-system-prompt` only when there truly is none, or omit both when the provider does not expose it.
4. Keep credentials in the runner environment. Use `--record-runner-argv` only after checking every argument for secrets.
5. Preserve prompts, responses, stderr, `run.json`, `grades.json`, `summary.json`, and (schema v4+) the grading-prompt file named by `grading_prompt.path` together in the run directory.
6. Validate all three artifacts with `--require-completed` before committing evidence.
7. Confirm the evidence validates from somewhere other than the checkout that produced it, for example from a second clone or from CI, with `--source-root` pointing at a clean checkout of the recorded commit. Schema-v5 bundles need nothing else because `skill_invocation_path` is recorded; for a v2–v4 with-skill bundle, note the absolute path from any prompt file's first line so reviewers can pass it as `--recorded-skill-path`.

### Revalidating evidence from another checkout

The validator compares eval-set and skill hashes with the files under `--source-root`, which defaults to the harness's own checkout. To revalidate historical evidence after those inputs have changed, point `--source-root` at a clean checkout of the commit recorded in `run.json` (a `git worktree` is enough); accepting an older schema does not substitute newer files for the original inputs. Every with-skill bundle committed before schema v5 was recorded at `/Users/gfargo/dev/gfargo/tui-design-skill/plugins/tui-design/skills/tui-design`, which is the value to pass as `--recorded-skill-path`; it is not needed for baseline bundles or for v5 bundles.

```bash
git worktree add /tmp/tui-design-63ac69f 63ac69f04c40ebd60308ca23d952106fd5d63677
bundle=evals/results/v1.7.0-lifecycle-comparison/v170-lifecycle-with-skill-r3
python3 scripts/eval_harness.py validate \
  --run "$bundle/run.json" \
  --grades "$bundle/grades.json" \
  --summary "$bundle/summary.json" \
  --require-completed \
  --source-root /tmp/tui-design-63ac69f \
  --recorded-skill-path /Users/gfargo/dev/gfargo/tui-design-skill/plugins/tui-design/skills/tui-design
```

The hashes recorded in the bundle are verified exactly as written; `--recorded-skill-path` only tells the validator which path the run's prompts embedded, and a wrong value fails with a prompt content mismatch.

`./scripts/validate-evidence.sh` does this for every bundle under `evals/results/`: it snapshots each recorded commit with `git archive`, passes the legacy path to pre-v5 with-skill bundles, and runs the full three-artifact validation. CI runs it on every push and pull request; it needs the complete git history, so run `git fetch --unshallow` first on a shallow clone.

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

For schema-v3+ grades, `grader.prompt_version` names the grading protocol and `grader.prompt_sha256` anchors its exact instructions. A model grader also records its provider, model, runner version, and generation metadata. Human grading uses `kind: "human"` and does not invent model fields. Schema-v4+ grades additionally require `grading_prompt: {"path": "grading-prompt.md", "sha256": "<same digest as grader.prompt_sha256>"}`, naming the committed file that carries those exact instructions. Grades and summaries carry the same schema version as their run manifest; v5 changes nothing in their rules beyond the version and URI.

Validation with a summary intentionally requires the corresponding grades so the harness can recompute totals and per-case results instead of trusting aggregate fields:

```bash
python3 scripts/eval_harness.py validate \
  --run evals/runs/RUN_ID/run.json \
  --grades evals/runs/RUN_ID/grades.json \
  --summary evals/runs/RUN_ID/summary.json \
  --require-completed
```
