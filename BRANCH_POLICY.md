# AI Lab Branch Policy

## Branch Roles

- `main` is the official stable development line.
- `ai/lab-life-skills-content` is an isolated AI experiment branch for content updates and small scoped optimizations.

## AI Contributor Rules

- Other AI agents may commit only to `ai/lab-life-skills-content`.
- Do not force push.
- Do not delete files.
- Do not delete branches.
- Do not merge directly into `main`.
- Do not rebase shared branches.
- Keep changes small, reviewable, and focused on content or low-risk tuning.

## Merge Policy

- All changes from this branch must be reviewed by a human or Codex before entering `main`.
- Any merge to `main` must happen only after review, tests, and explicit approval.
- If a change removes core files or rewrites system structure, treat it as high risk and stop for review.
