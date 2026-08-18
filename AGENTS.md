# Repository guidance

## GitHub release notes

Keep releases consistent with the existing `v1.5.1` patch and `v1.6.0` minor-release style.

- Title the release with the tag only: `vX.Y.Z`.
- Open with one sentence naming the release's purpose and line, without repeating the title.
- Use concise Markdown headings and bullets; describe shipped behavior, not the work session.
- Patch releases use `### Fixed` plus only the relevant optional sections: `### Release engineering` and `### Evaluation`.
- Minor releases use `## Highlights` with descriptive `###` subsections. Add `## Upgrade notes` only for user action and `## Release verification` for substantial validation evidence.
- Omit empty sections. Link to the changelog at the immutable release tag, never `main`.
- End with the artifact SHA-256 and a full comparison link. Create a draft, attach and verify the exact-tag asset, then publish.

Patch template:

```markdown
<One-sentence purpose for the X.Y line.>

### Fixed

- <User-visible correction.>

### Release engineering

- <Release-integrity change, when applicable.>

### Evaluation

- <Auditable evidence, when applicable.>

Asset SHA-256: `<sha256>`

See [CHANGELOG.md](https://github.com/gfargo/tui-design-skill/blob/vX.Y.Z/CHANGELOG.md) for the full change list.

**Full comparison:** https://github.com/gfargo/tui-design-skill/compare/vPREVIOUS...vX.Y.Z
```
