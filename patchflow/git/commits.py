from dataclasses import dataclass
import subprocess

from patchflow.git.repo import _run_git


@dataclass
class CommitRecord:
    sha: str
    message: str
    files: list[str]


def _files_for_commit(sha: str) -> list[str]:
    output = _run_git("diff-tree", "--no-commit-id", "--name-only", "-r", sha)
    return [line for line in output.splitlines() if line]


def list_branch_commits(base_branch: str, current_branch: str) -> list[CommitRecord]:
    if not current_branch:
        return []

    try:
        merge_base = _run_git("merge-base", current_branch, base_branch)
        log_output = _run_git(
            "log",
            "--reverse",
            "--format=%H%x1f%s",
            f"{merge_base}..{current_branch}",
        )
    except subprocess.CalledProcessError:
        return []

    commits: list[CommitRecord] = []
    for line in log_output.splitlines():
        if not line.strip():
            continue
        sha, message = line.split("\x1f", maxsplit=1)
        commits.append(
            CommitRecord(
                sha=sha,
                message=message,
                files=_files_for_commit(sha),
            )
        )
    return commits
