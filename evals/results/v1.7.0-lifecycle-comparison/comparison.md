# Repeated lifecycle comparison

This study measures the consistency of the v1.7.0 lifecycle guidance against a matched no-skill baseline. It does not alter the immutable single-snapshot v1.7.0 release evidence.

## Protocol

- Source snapshot: clean commit `63ac69f04c40ebd60308ca23d952106fd5d63677`.
- Eval set: `evals/v170-lifecycle-evals.json`, SHA-256 `1bab1181943831a35d45acdabc7bdcdef0afa99a572813f4a84a2e79a4115945`.
- Skill snapshot: `plugins/tui-design/skills/tui-design`, tree SHA-256 `8bb1f093f84be90ebb4a4a54071ff8db196afdd7ade70c50a54c769b8dcf4156`.
- Runner: OpenAI Codex desktop CLI `0.147.0-alpha.6.5`, `gpt-5.6-terra`, high reasoning, 900-second trial timeout. The runner exposed neither seed nor temperature.
- Design: five cases, three repetitions per case and condition, 15 trials and 75 independently graded assertions per condition.
- Grading: direct rubric protocol `v170-lifecycle-direct-rubric-v1`; every boolean includes an evidence note. Both schema-v4 bundles validate with `--require-completed`.

Both conditions ran from the same empty workspace. Automatic skill instructions, bundled skills, plugins, and skill search were disabled at the runner boundary. Baseline prompts were unchanged. With-skill prompts differed only by the harness's explicit instruction to read the immutable skill path. This isolation matters: an earlier local attempt was discarded after its trace proved that the globally installed `tui-design` skill had activated inside the nominal baseline.

## Results

| Case | Baseline | With skill | Difference |
|---|---:|---:|---:|
| Bubble Tea editor handoff | 10/12 (83.3%) | 12/12 (100.0%) | +16.7 pp |
| Ratatui editor reader | 15/15 (100.0%) | 14/15 (93.3%) | -6.7 pp |
| Textual portable suspension | 9/15 (60.0%) | 13/15 (86.7%) | +26.7 pp |
| Ink terminal suspension | 15/15 (100.0%) | 15/15 (100.0%) | 0.0 pp |
| Cross-framework signal boundaries | 14/18 (77.8%) | 15/18 (83.3%) | +5.6 pp |
| **Aggregate** | **63/75 (84.0%)** | **69/75 (92.0%)** | **+8.0 pp** |

The observed aggregate lift is six additional passing assertions. It is concentrated in Bubble Tea's `tea.Interrupt`/`ErrInterrupted` distinction and Textual's unsupported-suspension and exit-code contracts. Ink was saturated in both conditions. The with-skill condition had one Ratatui regression: prose requested preserving both child and re-entry failures, but one code branch discarded a nonzero child status when re-entry also failed.

Both conditions still struggled to name a concrete Windows alternative to Unix job control in the cross-framework case. Two with-skill Textual repetitions also reloaded after editor handoff but did not discuss externally mutable state after foreground-process resume.

## Repetition variance

| Repetition | Baseline | With skill | Difference |
|---|---:|---:|---:|
| 1 | 21/25 (84.0%) | 23/25 (92.0%) | +8.0 pp |
| 2 | 21/25 (84.0%) | 23/25 (92.0%) | +8.0 pp |
| 3 | 21/25 (84.0%) | 23/25 (92.0%) | +8.0 pp |

For aggregate assertion pass rate across repetitions, both conditions have population variance `0.0`, standard deviation `0.0`, and range `0.0` percentage points. Case-level misses varied between repetitions even though the aggregate totals did not.

These measurements support a narrow claim: under this runner, model, prompt set, and three-repetition protocol, explicit use of the skill increased the observed assertion pass rate from 84% to 92%. They do not establish a population-level causal effect, generalize to other models or hosts, or imply that every case improved.

## Evidence bundles

- [`v170-lifecycle-baseline-r3/`](v170-lifecycle-baseline-r3/) preserves the baseline manifest, prompts, responses, stderr, grading prompt, grades, and summary.
- [`v170-lifecycle-with-skill-r3/`](v170-lifecycle-with-skill-r3/) preserves the matched with-skill artifacts.
