# Patchflow

Patchflow is a local-first CLI that analyzes a branch, detects probable scope
drift, creates a clean branch from intended changes, and explains simple merge
blockers for an existing PR.

## Current Commands

Patchflow currently exposes three commands:

- `patchflow analyze`
  Inspect the current branch, group changes into clusters, and surface likely
  scope drift.
- `patchflow clean`
  Create a clean branch from the selected cluster without modifying the
  original branch.
- `patchflow status`
  Fetch live GitHub PR status and summarize simple blockers.
- `patchflow doctor`
  Inspect whether Patchflow can run cleanly in the current environment and repo.
- `patchflow tui`
  Launch a minimal interactive terminal UI for analyzing clusters and creating a
  clean branch.

Patchflow also includes a minimal VS Code extension in
[`vscode-extension/`](/Users/neilnair/Documents/Playground/patchflow/vscode-extension)
that consumes the CLI's JSON interface.

## What Works Today

- Real git-backed branch analysis
- Explicit cluster selection via `--cluster`
- Safe clean-branch creation from committed changes
- Live GitHub PR status for public repos or repos accessible via
  `GITHUB_TOKEN` / `GH_TOKEN`
- Minimal Textual-based terminal UI for analyze + clean preview
- Minimal VS Code webview extension powered by `analyze --json`, `clean --json`,
  and `status --json`
- Black-box CLI tests over disposable git repos

## What It Does Not Do Yet

- Merge prediction
- Maintainer behavior modeling
- Automatic handling of uncommitted-only changes in `clean`
- Automatic reviewer assignment
- GitHub writes such as opening PRs or commenting

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
patchflow --help
```

## Usage

### Analyze a branch

```bash
patchflow analyze
patchflow analyze --cluster 2
patchflow analyze --json
```

Example output:

```text
Branch: feature/test-clean
Status: DIRTY
Confidence: LOW

Scope Analysis:
- 2 change clusters detected
- likely unrelated changes present
- 2 changed files detected

Clusters:
- [1] cluster-2 score=12.00 confidence=LOW (selected)
  commit: docs: add notes
  file: notes.md
- [2] cluster-1 score=10.00 confidence=LOW
  commit: feat: update app
  file: app.txt
```

### Create a clean branch

```bash
patchflow clean --dry-run
patchflow clean --cluster 2 --branch-name patchflow/clean-feature --yes
patchflow clean --dry-run --json
```

Safety rules:

- Patchflow never rewrites the original branch.
- Patchflow creates a new branch from the detected base branch.
- Patchflow refuses low-confidence cleans unless you pass `--cluster`.
- Patchflow refuses uncommitted-only clean operations in V1.

### Check PR status

```bash
patchflow status --pr 22894
patchflow status --pr https://github.com/google-gemini/gemini-cli/pull/22894
patchflow status --json --pr 22894
```

If `--pr` is omitted, Patchflow tries to infer an open PR from the current
branch on the `origin` GitHub remote.

### Run environment diagnostics

```bash
patchflow doctor
patchflow doctor --json
```

This reports:

- whether `git` is available
- whether the current directory is a git worktree
- current branch/base context when available
- whether GitHub auth is likely available for private-repo status checks

### Launch the terminal UI

```bash
patchflow tui
patchflow tui --branch-name patchflow/clean-demo
```

The current TUI supports:

- branch summary
- cluster list with selection
- clean preview pane
- PR status pane
- refresh
- PR status refresh
- clean branch creation

The VS Code extension currently supports:

- analyze + cluster selection
- clean preview
- clean branch creation
- clean branch name override
- PR status via auto-detect or manual PR number / URL input
- local environment diagnostics via `patchflow doctor`

If the extension cannot find the CLI, set `Patchflow > Cli Path` in VS Code
settings to point at the executable you want it to run.

## Structured Output

`analyze`, `clean`, and `status` all support `--json` for machine-readable output.

This is the current integration surface for editor tooling, scripts, and future
UI layers.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

Build the VS Code extension:

```bash
cd vscode-extension
npm install
npm run build
npm test
```

## Repository Layout

```text
patchflow/
  commands/   CLI commands
  git/        git inspection helpers
  analysis/   clustering and scope analysis
  cleaning/   clean-branch creation
  github/     GitHub PR status integration
  utils/      output rendering
tests/        CLI and helper tests
```
