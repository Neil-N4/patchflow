from patchflow.analysis.scope import ScopeAnalysisResult
from patchflow.cleaning.branch_builder import default_clean_branch_name
from patchflow.utils.output import render_clean_preview


def branch_summary_text(result: ScopeAnalysisResult) -> str:
    lines = [
        f"Branch: {result.branch.current_branch}",
        f"Base: {result.branch.base_branch}",
        f"Status: {result.status}",
        f"Confidence: {result.confidence}",
        f"Ahead: {result.branch.ahead_by}",
        f"Behind: {result.branch.behind_by}",
    ]
    if result.branch.has_uncommitted_changes:
        lines.append("Worktree: uncommitted changes present")
    return "\n".join(lines)


def cluster_label(result: ScopeAnalysisResult, index: int) -> str:
    cluster = result.clusters[index]
    selected = " *" if result.selected_cluster_index == index else ""
    return (
        f"[{index + 1}] {cluster.label}{selected} | "
        f"score={cluster.score:.2f} | "
        f"confidence={cluster.confidence} | "
        f"commits={len(cluster.commits)} | files={len(cluster.files)}"
    )


def detail_text(result: ScopeAnalysisResult, branch_name: str | None) -> str:
    clean_branch_name = branch_name or default_clean_branch_name(result.branch.current_branch)
    return (
        f"Planned clean branch: {clean_branch_name}\n\n"
        f"{render_clean_preview(result, branch_name)}"
    )
