from dataclasses import dataclass

from patchflow.analysis.clustering import CommitCluster, cluster_commits
from patchflow.git.commits import CommitRecord, list_branch_commits
from patchflow.git.diff import list_changed_files, list_worktree_files
from patchflow.git.repo import BranchContext, get_branch_context


@dataclass
class ScopeAnalysisResult:
    branch: BranchContext
    status: str
    confidence: str
    clusters: list[CommitCluster]
    selected_cluster: CommitCluster | None
    selected_cluster_index: int | None
    changed_files: list[str]
    other_files: list[str]
    recommendations: list[str]


def _resolve_selected_cluster(
    clusters: list[CommitCluster],
    cluster_index: int | None,
) -> tuple[int | None, CommitCluster | None]:
    if not clusters:
        return None, None

    if cluster_index is None:
        return 0, clusters[0]

    if cluster_index < 1 or cluster_index > len(clusters):
        raise ValueError(f"Cluster {cluster_index} is out of range.")

    resolved_index = cluster_index - 1
    return resolved_index, clusters[resolved_index]


def analyze_branch_scope(cluster_index: int | None = None) -> ScopeAnalysisResult:
    branch = get_branch_context()
    commits = list_branch_commits(
        base_branch=branch.base_branch,
        current_branch=branch.current_branch,
    )
    worktree_files = list_worktree_files()
    if worktree_files:
        commits.append(
            CommitRecord(
                sha="WORKTREE",
                message="uncommitted changes",
                files=worktree_files,
            )
        )

    changed_files = list_changed_files()
    clusters = cluster_commits(commits)
    selected_cluster_index, selected_cluster = _resolve_selected_cluster(
        clusters,
        cluster_index,
    )
    selected_files = set(selected_cluster.files if selected_cluster else [])
    other_files = [path for path in changed_files if path not in selected_files]

    recommendations: list[str] = []
    if branch.behind_by > 0:
        recommendations.append("update branch")
    if len(clusters) > 1 or other_files or branch.has_uncommitted_changes:
        recommendations.append("clean branch")
    if not recommendations:
        recommendations.append("wait")

    status = "DIRTY" if len(clusters) > 1 or other_files or branch.has_uncommitted_changes else "CLEAN"
    confidence = selected_cluster.confidence if selected_cluster else "LOW"

    return ScopeAnalysisResult(
        branch=branch,
        status=status,
        confidence=confidence,
        clusters=clusters,
        selected_cluster=selected_cluster,
        selected_cluster_index=selected_cluster_index,
        changed_files=changed_files,
        other_files=other_files,
        recommendations=recommendations,
    )
