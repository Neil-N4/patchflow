from patchflow.analysis.scope import ScopeAnalysisResult


def create_clean_branch(
    result: ScopeAnalysisResult,
    branch_name: str | None = None,
) -> str:
    clean_branch_name = branch_name or f"patchflow/clean-{result.branch.current_branch}"
    return (
        f"Created: {clean_branch_name}\n\n"
        "Included:\n"
        f"- {len(result.selected_cluster.commits) if result.selected_cluster else 0} commits\n"
        f"- {len(result.selected_cluster.files) if result.selected_cluster else 0} files\n\n"
        "Safe: original branch unchanged"
    )
