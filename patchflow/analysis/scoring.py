def score_cluster(
    file_overlap_density: float,
    recency_weight: int,
    path_concentration: float,
    message_similarity: float,
    commit_count: int,
) -> float:
    return (
        file_overlap_density * 4
        + recency_weight * 0.75
        + path_concentration * 3
        + message_similarity
        + commit_count * 2.5
    )
