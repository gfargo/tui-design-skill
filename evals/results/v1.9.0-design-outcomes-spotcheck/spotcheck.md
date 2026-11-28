# Grader spot-check

A deterministic 40% sample of trials (seed 79) from 4 bundles, re-graded by OpenAI `gpt-6.1-sol` with each bundle's own grading prompt, compared with the original claude-opus-5-5 grades.

- **Assertions compared:** 258
- **Agreement:** 243/258 (94.2%)
- **Cohen's kappa:** 0.620
- **Pass rate:** Claude grader 92.2%, Codex grader 91.1%

## Pass rate by answering provider and condition

| Answers from | Condition | Assertions | Claude grader | Codex grader |
|---|---|---:|---:|---:|
| Anthropic | baseline | 63 | 95.2% | 93.7% |
| Anthropic | with-skill | 64 | 95.3% | 95.3% |
| OpenAI | baseline | 64 | 81.2% | 79.7% |
| OpenAI | with-skill | 67 | 97.0% | 95.5% |

## Per bundle

| Bundle | Trials | Assertions | Agreement | Kappa |
|---|---:|---:|---:|---:|
| `v190-design-outcomes-claude-baseline-r3` | 10 | 63 | 98.4% | 0.849 |
| `v190-design-outcomes-claude-with-skill-r3` | 10 | 64 | 93.8% | 0.301 |
| `v190-design-outcomes-codex-baseline-r3` | 10 | 64 | 92.2% | 0.752 |
| `v190-design-outcomes-codex-with-skill-r3` | 10 | 67 | 92.5% | -0.037 |

## Disagreements (15)

- `partial-failure-screen-r3` in `v190-design-outcomes-claude-baseline-r3`, assertion 6: Claude **pass**, Codex **fail**. States, in the sketch or the text, how many of the five servers answered (three of five)
- `focus-without-color-r2` in `v190-design-outcomes-claude-with-skill-r3`, assertion 5: Claude **pass**, Codex **fail**. Uses no more than two different cues to mark focus, instead of stacking several
- `footer-at-two-widths-r2` in `v190-design-outcomes-claude-with-skill-r3`, assertion 6: Claude **fail**, Codex **pass**. The 40-column line shows fewer hints than the 80-column line, and the hints it drops are among the least frequently used
- `log-viewer-from-scratch-r2` in `v190-design-outcomes-claude-with-skill-r3`, assertion 5: Claude **fail**, Codex **pass**. Describes what the user sees when no log lines have arrived yet, and what they can do
- `delete-confirmation-r2` in `v190-design-outcomes-claude-with-skill-r3`, assertion 4: Claude **pass**, Codex **fail**. The sketch is no wider than 64 characters (80 percent of the terminal width)
- `count-the-borders-r1` in `v190-design-outcomes-codex-baseline-r3`, assertion 1: Claude **fail**, Codex **pass**. States that a job row sits behind three borders (the outer frame, the pane box, and the inner box), or gives a count of 3 for the nesting
- `count-the-borders-r1` in `v190-design-outcomes-codex-baseline-r3`, assertion 5: Claude **pass**, Codex **fail**. The redesigned screen still shows all three job names with their pass or fail state, and the job, status, and duration details
- `count-the-borders-r2` in `v190-design-outcomes-codex-baseline-r3`, assertion 7: Claude **fail**, Codex **pass**. No line of the redesigned screen is wider than 72 characters
- `sixty-column-sketch-r2` in `v190-design-outcomes-codex-baseline-r3`, assertion 3: Claude **pass**, Codex **fail**. The widths of the panes visible side by side in the sketch add up to no more than 60 columns, and the commit list in it is at least 40 columns wide as the spec requires
- `sixty-column-sketch-r3` in `v190-design-outcomes-codex-baseline-r3`, assertion 3: Claude **pass**, Codex **fail**. The widths of the panes visible side by side in the sketch add up to no more than 60 columns, and the commit list in it is at least 40 columns wide as the spec requires
- `count-the-borders-r3` in `v190-design-outcomes-codex-with-skill-r3`, assertion 3: Claude **fail**, Codex **pass**. Points out that the > marker appears on all three rows, so it separates none of them from the others
- `count-the-borders-r3` in `v190-design-outcomes-codex-with-skill-r3`, assertion 5: Claude **pass**, Codex **fail**. The redesigned screen still shows all three job names with their pass or fail state, and the job, status, and duration details
- `footer-at-two-widths-r2` in `v190-design-outcomes-codex-with-skill-r3`, assertion 6: Claude **pass**, Codex **fail**. The 40-column line shows fewer hints than the 80-column line, and the hints it drops are among the least frequently used
- `log-viewer-from-scratch-r3` in `v190-design-outcomes-codex-with-skill-r3`, assertion 5: Claude **fail**, Codex **pass**. Describes what the user sees when no log lines have arrived yet, and what they can do
- `delete-confirmation-r2` in `v190-design-outcomes-codex-with-skill-r3`, assertion 4: Claude **pass**, Codex **fail**. The sketch is no wider than 64 characters (80 percent of the terminal width)
