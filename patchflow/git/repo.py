from dataclasses import dataclass
import subprocess


@dataclass
class BranchContext:
    current_branch: str
    base_branch: str
    ahead_by: int
    behind_by: int
    has_uncommitted_changes: bool


def _run_git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.rstrip("\n")


def _git_ok(*args: str) -> bool:
    try:
        _run_git(*args)
        return True
    except subprocess.CalledProcessError:
        return False


def detect_base_branch() -> str:
    try:
        origin_head = _run_git("symbolic-ref", "refs/remotes/origin/HEAD")
        return origin_head.rsplit("/", maxsplit=1)[-1]
    except subprocess.CalledProcessError:
        pass

    for candidate in ("main", "master"):
        if _git_ok("rev-parse", "--verify", candidate):
            return candidate
    return "main"


def has_uncommitted_changes() -> bool:
    return bool(_run_git("status", "--porcelain"))


def get_branch_context() -> BranchContext:
    current_branch = _run_git("branch", "--show-current")
    base_branch = detect_base_branch()

    ahead_by = 0
    behind_by = 0
    if current_branch and base_branch and current_branch != base_branch:
        try:
            behind_output = _run_git(
                "rev-list",
                "--left-right",
                "--count",
                f"{current_branch}...{base_branch}",
            )
            ahead, behind = behind_output.split()
            ahead_by = int(ahead)
            behind_by = int(behind)
        except subprocess.CalledProcessError:
            ahead_by = 0
            behind_by = 0

    return BranchContext(
        current_branch=current_branch,
        base_branch=base_branch,
        ahead_by=ahead_by,
        behind_by=behind_by,
        has_uncommitted_changes=has_uncommitted_changes(),
    )
