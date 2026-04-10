import json

from patchflow.analysis.scope import ScopeAnalysisResult
from patchflow.cleaning.branch_builder import CleanBranchSummary, default_clean_branch_name
from patchflow.github.pr_status import PRStatusResult


def analysis_to_dict(result: ScopeAnalysisResult) -> dict[str, object]:
    return {
        "branch": {
            "current": result.branch.current_branch,
            "base": result.branch.base_branch,
            "ahead_by": result.branch.ahead_by,
            "behind_by": result.branch.behind_by,
            "has_uncommitted_changes": result.branch.has_uncommitted_changes,
        },
        "status": result.status,
        "confidence": result.confidence,
        "selected_cluster_index": (
            result.selected_cluster_index + 1
            if result.selected_cluster_index is not None
            else None
        ),
        "changed_files": result.changed_files,
        "worktree_files": result.worktree_files,
        "other_files": result.other_files,
        "recommendations": result.recommendations,
        "clusters": [
            {
                "index": index,
                "label": cluster.label,
                "score": round(cluster.score, 4),
                "confidence": cluster.confidence,
                "commits": [
                    {
                        "sha": commit.sha,
                        "message": commit.message,
                        "files": commit.files,
                    }
                    for commit in cluster.commits
                ],
                "files": cluster.files,
            }
            for index, cluster in enumerate(result.clusters, start=1)
        ],
    }


def render_analysis_json(result: ScopeAnalysisResult) -> str:
    return json.dumps(analysis_to_dict(result), indent=2, sort_keys=True)


def render_analysis(result: ScopeAnalysisResult) -> str:
    selected_files = result.selected_cluster.files if result.selected_cluster else []
    selected_block = "\n".join(f"- {path}" for path in selected_files) or "- none"
    other_block = "\n".join(f"- {path}" for path in result.other_files) or "- none"
    rec_block = "\n".join(f"- {item}" for item in result.recommendations)
    cluster_block = _render_clusters(result)
    worktree_block = "\n".join(f"- {path}" for path in result.worktree_files) or "- none"
    branch_notes = [f"- {result.branch.behind_by} commits behind {result.branch.base_branch}"]
    if result.branch.ahead_by:
        branch_notes.append(f"- {result.branch.ahead_by} commits ahead of {result.branch.base_branch}")
    if result.branch.has_uncommitted_changes:
        branch_notes.append("- uncommitted changes present")
    branch_block = "\n".join(branch_notes)
    scope_note = (
        "- likely unrelated changes present"
        if len(result.clusters) > 1 or result.other_files
        else "- no obvious unrelated changes detected"
    )

    return (
        f"Branch: {result.branch.current_branch}\n"
        f"Status: {result.status}\n"
        f"Confidence: {result.confidence}\n\n"
        "Scope Analysis:\n"
        f"- {len(result.clusters)} change clusters detected\n"
        f"{scope_note}\n"
        f"- {len(result.changed_files)} changed files detected\n\n"
        "Clusters:\n"
        f"{cluster_block}\n\n"
        "Worktree changes:\n"
        f"{worktree_block}\n\n"
        "Primary cluster (selected):\n"
        f"{selected_block}\n\n"
        "Other changes:\n"
        f"{other_block}\n\n"
        "Branch Status:\n"
        f"{branch_block}\n\n"
        "Recommendation:\n"
        f"{rec_block}"
    )


def render_clean_preview(
    result: ScopeAnalysisResult,
    branch_name: str | None,
) -> str:
    selected_commits = result.selected_cluster.commits if result.selected_cluster else []
    selected_files = result.selected_cluster.files if result.selected_cluster else []
    clean_branch_name = branch_name or default_clean_branch_name(result.branch.current_branch)
    selected_cluster_position = result.selected_cluster_index

    excluded_commits = [
        commit.message
        for index, cluster in enumerate(result.clusters)
        if index != selected_cluster_position
        for commit in cluster.commits
        if commit.sha != "WORKTREE"
    ]
    excluded_files = [path for path in result.other_files]

    commit_block = "\n".join(f"- {commit.message}" for commit in selected_commits) or "- none"
    file_block = "\n".join(f"- {path}" for path in selected_files) or "- none"
    excluded_commit_block = "\n".join(f"- {message}" for message in excluded_commits) or "- none"
    excluded_file_block = "\n".join(f"- {path}" for path in excluded_files) or "- none"

    return (
        f"Planned branch: {clean_branch_name}\n\n"
        f"Selected cluster: {((result.selected_cluster_index or 0) + 1) if result.selected_cluster_index is not None else 'auto'}\n\n"
        "Selected commits:\n"
        f"{commit_block}\n\n"
        "Excluded commits:\n"
        f"{excluded_commit_block}\n\n"
        "Selected files:\n"
        f"{file_block}\n\n"
        "Excluded files:\n"
        f"{excluded_file_block}\n\n"
        "Safe: original branch unchanged"
    )


def clean_preview_to_dict(
    result: ScopeAnalysisResult,
    branch_name: str | None,
) -> dict[str, object]:
    selected_commits = result.selected_cluster.commits if result.selected_cluster else []
    selected_files = result.selected_cluster.files if result.selected_cluster else []
    clean_branch_name = branch_name or default_clean_branch_name(result.branch.current_branch)
    selected_cluster = (
        result.selected_cluster_index + 1
        if result.selected_cluster_index is not None
        else None
    )

    excluded_commits = [
        {
            "sha": commit.sha,
            "message": commit.message,
            "files": commit.files,
        }
        for index, cluster in enumerate(result.clusters)
        if index != result.selected_cluster_index
        for commit in cluster.commits
        if commit.sha != "WORKTREE"
    ]

    selected_commit_payload = [
        {
            "sha": commit.sha,
            "message": commit.message,
            "files": commit.files,
        }
        for commit in selected_commits
    ]

    return {
        "branch_name": clean_branch_name,
        "selected_cluster_index": selected_cluster,
        "selected_commits": selected_commit_payload,
        "excluded_commits": excluded_commits,
        "selected_files": selected_files,
        "excluded_files": result.other_files,
        "safe": True,
    }


def render_clean_preview_json(
    result: ScopeAnalysisResult,
    branch_name: str | None,
) -> str:
    return json.dumps(clean_preview_to_dict(result, branch_name), indent=2, sort_keys=True)


def _render_clusters(result: ScopeAnalysisResult) -> str:
    if not result.clusters:
        return "- none"

    sections: list[str] = []
    for index, cluster in enumerate(result.clusters, start=1):
        header = f"- [{index}] {cluster.label} score={cluster.score:.2f} confidence={cluster.confidence}"
        if result.selected_cluster_index == index - 1:
            header += " (selected)"
        commit_lines = [f"  commit: {commit.message}" for commit in cluster.commits]
        file_lines = [f"  file: {path}" for path in cluster.files]
        sections.append("\n".join([header, *commit_lines, *file_lines]))
    return "\n".join(sections)


def render_status(result: PRStatusResult) -> str:
    checks = "\n".join(f"- {item}" for item in result.checks)
    reviews = "\n".join(f"- {item}" for item in result.reviews)
    branch = "\n".join(f"- {item}" for item in result.branch)
    conflicts = "\n".join(f"- {item}" for item in result.conflicts)

    return (
        f"PR Status: {result.status}\n\n"
        "Checks:\n"
        f"{checks}\n\n"
        "Reviews:\n"
        f"{reviews}\n\n"
        "Branch:\n"
        f"{branch}\n\n"
        "Conflicts:\n"
        f"{conflicts}\n\n"
        f"Recommendation:\n-> {result.recommendation}"
    )


def status_to_dict(result: PRStatusResult) -> dict[str, object]:
    return {
        "status": result.status,
        "checks": result.checks,
        "reviews": result.reviews,
        "branch": result.branch,
        "conflicts": result.conflicts,
        "recommendation": result.recommendation,
    }


def render_status_json(result: PRStatusResult) -> str:
    return json.dumps(status_to_dict(result), indent=2, sort_keys=True)


def clean_summary_to_dict(summary: CleanBranchSummary) -> dict[str, object]:
    return {
        "success": True,
        "branch_name": summary.branch_name,
        "original_branch": summary.original_branch,
        "current_branch": summary.current_branch,
        "included_commits": summary.included_commits,
        "included_files": summary.included_files,
        "safe": True,
    }


def render_clean_summary_json(summary: CleanBranchSummary) -> str:
    return json.dumps(clean_summary_to_dict(summary), indent=2, sort_keys=True)


def clean_error_to_dict(message: str, *, code: str) -> dict[str, object]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }


def render_clean_error_json(message: str, *, code: str) -> str:
    return json.dumps(clean_error_to_dict(message, code=code), indent=2, sort_keys=True)
