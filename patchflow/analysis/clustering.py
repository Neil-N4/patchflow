from dataclasses import dataclass

from patchflow.analysis.scoring import score_cluster
from patchflow.git.commits import CommitRecord


@dataclass
class CommitCluster:
    label: str
    commits: list[CommitRecord]
    files: list[str]
    score: float
    confidence: str


def _top_level_path(path: str) -> str:
    return path.split("/", maxsplit=1)[0]


def _message_tokens(message: str) -> set[str]:
    return {token for token in message.lower().replace(":", " ").replace("-", " ").split() if token}


def _related_to_cluster(commit: CommitRecord, cluster: CommitCluster) -> bool:
    commit_files = set(commit.files)
    cluster_files = set(cluster.files)
    if commit_files & cluster_files:
        return True

    commit_roots = {_top_level_path(path) for path in commit.files}
    cluster_roots = {_top_level_path(path) for path in cluster.files}
    return bool(commit_roots & cluster_roots)


def _clusters_are_ambiguous(primary: CommitCluster, secondary: CommitCluster) -> bool:
    if len(primary.commits) == 1 and len(secondary.commits) == 1:
        return True

    primary_files = set(primary.files)
    secondary_files = set(secondary.files)
    if not (primary_files & secondary_files) and abs(primary.score - secondary.score) < 2.5:
        return True

    return False


def _cluster_score(
    cluster: CommitCluster,
    total_commits: int,
    commit_positions: dict[str, int],
) -> float:
    file_count = len(cluster.files)
    commit_count = len(cluster.commits)
    overlap_density = commit_count / max(file_count, 1)
    newest_position = max((commit_positions[commit.sha] for commit in cluster.commits), default=0)
    recency_weight = max(newest_position + 1, 1)

    roots = [_top_level_path(path) for path in cluster.files]
    dominant_root_count = max((roots.count(root) for root in set(roots)), default=0)
    path_concentration = dominant_root_count / max(len(roots), 1)

    token_sets = [_message_tokens(commit.message) for commit in cluster.commits]
    common_tokens = set.intersection(*token_sets) if token_sets else set()
    message_similarity = len(common_tokens) / max(len(set.union(*token_sets)) if token_sets else 1, 1)

    return score_cluster(
        file_overlap_density=overlap_density,
        recency_weight=recency_weight,
        path_concentration=path_concentration,
        message_similarity=message_similarity,
    )


def cluster_commits(commits: list[CommitRecord]) -> list[CommitCluster]:
    if not commits:
        return []

    clusters: list[CommitCluster] = []
    for commit in commits:
        matching_cluster = next(
            (cluster for cluster in clusters if _related_to_cluster(commit, cluster)),
            None,
        )
        if matching_cluster is None:
            clusters.append(
                CommitCluster(
                    label=f"cluster-{len(clusters) + 1}",
                    commits=[commit],
                    files=sorted(set(commit.files)),
                    score=0.0,
                    confidence="LOW",
                )
            )
            continue

        matching_cluster.commits.append(commit)
        matching_cluster.files = sorted(set(matching_cluster.files) | set(commit.files))

    total_commits = len(commits)
    commit_positions = {commit.sha: index for index, commit in enumerate(commits)}
    for cluster in clusters:
        cluster.score = _cluster_score(cluster, total_commits, commit_positions)

    ranked = sorted(clusters, key=lambda cluster: cluster.score, reverse=True)
    if len(ranked) == 1:
        ranked[0].confidence = "HIGH"
        return ranked

    score_gap = ranked[0].score - ranked[1].score
    if _clusters_are_ambiguous(ranked[0], ranked[1]):
        ranked[0].confidence = "LOW"
    else:
        ranked[0].confidence = "HIGH" if score_gap >= 2 else "MEDIUM" if score_gap >= 0.75 else "LOW"
    for cluster in ranked[1:]:
        cluster.confidence = "LOW"
    return ranked
