from dataclasses import dataclass
import subprocess

from patchflow.analysis.scope import ScopeAnalysisResult


@dataclass
class CleanBranchSummary:
    branch_name: str
    included_commits: int
    included_files: int


class CleanBranchError(RuntimeError):
    """Raised when Patchflow cannot safely create a clean branch."""


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _branch_exists(branch_name: str) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", branch_name],
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _sanitize_branch_name(current_branch: str) -> str:
    sanitized = current_branch.replace("/", "-").replace("_", "-")
    return sanitized.strip("-") or "current"


def default_clean_branch_name(current_branch: str) -> str:
    return f"patchflow/clean-{_sanitize_branch_name(current_branch)}"


def render_clean_summary(summary: CleanBranchSummary) -> str:
    return (
        f"Created: {summary.branch_name}\n\n"
        "Included:\n"
        f"- {summary.included_commits} commits\n"
        f"- {summary.included_files} files\n\n"
        "Safe: original branch unchanged"
    )


def create_clean_branch(
    result: ScopeAnalysisResult,
    branch_name: str | None = None,
) -> CleanBranchSummary:
    if result.selected_cluster is None:
        raise CleanBranchError("No selected cluster is available to clean.")

    commit_shas = [
        commit.sha
        for commit in result.selected_cluster.commits
        if commit.sha != "WORKTREE"
    ]
    if not commit_shas:
        raise CleanBranchError(
            "Patchflow V1 cannot clean uncommitted-only changes. Commit the branch changes first."
        )

    clean_branch_name = branch_name or default_clean_branch_name(
        result.branch.current_branch
    )
    if _branch_exists(clean_branch_name):
        raise CleanBranchError(
            f"Branch '{clean_branch_name}' already exists. Choose another name with --branch-name."
        )

    original_branch = result.branch.current_branch
    base_branch = result.branch.base_branch

    try:
        _run_git("switch", "-c", clean_branch_name, base_branch)
        for sha in commit_shas:
            _run_git("cherry-pick", sha)
    except subprocess.CalledProcessError as exc:
        subprocess.run(["git", "cherry-pick", "--abort"], capture_output=True, text=True)
        subprocess.run(["git", "switch", original_branch], capture_output=True, text=True)
        subprocess.run(["git", "branch", "-D", clean_branch_name], capture_output=True, text=True)
        stderr = exc.stderr.strip() if exc.stderr else "unknown git error"
        raise CleanBranchError(f"Failed to create clean branch: {stderr}") from exc

    _run_git("switch", original_branch)
    return CleanBranchSummary(
        branch_name=clean_branch_name,
        included_commits=len(commit_shas),
        included_files=len(result.selected_cluster.files),
    )
