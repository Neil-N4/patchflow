from dataclasses import dataclass

from patchflow.git.commits import CommitRecord


@dataclass
class CommitCluster:
    label: str
    commits: list[CommitRecord]
    files: list[str]
    confidence: str


def cluster_commits(commits: list[CommitRecord]) -> list[CommitCluster]:
    if not commits:
        return []

    primary_files = sorted({path for commit in commits for path in commit.files})
    return [
        CommitCluster(
            label="primary",
            commits=commits,
            files=primary_files,
            confidence="LOW",
        )
    ]
