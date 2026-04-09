# Patchflow

Patchflow is a local-first CLI that analyzes a branch, detects probable scope
drift, creates a clean branch from intended changes, and explains simple merge
blockers for an existing PR.

## V1 Scope

Patchflow V1 does exactly three things:

- `patchflow analyze`: inspect the current branch and flag likely scope drift
- `patchflow clean`: create a clean branch from the selected changes
- `patchflow status`: summarize simple PR blockers for an existing PR

It does not attempt merge prediction, maintainer modeling, or issue scoring.

## Planned UX

```text
$ patchflow analyze
Branch: feature/fix-debug
Status: DIRTY

Scope Analysis:
- 2 change clusters detected
- likely unrelated changes present

Primary cluster (selected):
- src/debug/config.ts
- package.json

Other changes:
- README.md
- formatting (12 files)

Branch Status:
- 7 commits behind main

Recommendation:
- clean branch
- update branch
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
patchflow --help
```

## Repository Layout

```text
patchflow/
  commands/
  git/
  analysis/
  cleaning/
  github/
  utils/
```
