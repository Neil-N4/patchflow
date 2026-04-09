from dataclasses import dataclass

from patchflow.analysis.clustering import CommitCluster, cluster_commits
from patchflow.git.commits import CommitRecord
from patchflow.git.repo import BranchContext, get_branch_context


@dataclass
class ScopeAnalysisResult:
    branch: BranchContext
    status: str
    confidence: str
    clusters: list[CommitCluster]
    selected_cluster: CommitCluster | None
    other_files: list[str]
    recommendations: list[str]


def analyze_branch_scope() -> ScopeAnalysisResult:
    branch = get_branch_context()

    commits = [
        CommitRecord(
            sha="HEAD",
            message="working tree snapshot",
            files=["README.md"],
        )
    ]
    clusters = cluster_commits(commits)
    selected_cluster = clusters[0] if clusters else None

    recommendations = ["clean branch"]
    if branch.behind_by > 0:
        recommendations.append("update branch")
    else:
        recommendations.append("wait")

    return ScopeAnalysisResult(
        branch=branch,
        status="DIRTY",
        confidence=selected_cluster.confidence if selected_cluster else "LOW",
        clusters=clusters,
        selected_cluster=selected_cluster,
        other_files=[],
        recommendations=recommendations,
    )
