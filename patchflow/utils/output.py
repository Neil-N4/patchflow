from patchflow.analysis.scope import ScopeAnalysisResult
from patchflow.github.pr_status import PRStatusResult


def render_analysis(result: ScopeAnalysisResult) -> str:
    selected_files = result.selected_cluster.files if result.selected_cluster else []
    selected_block = "\n".join(f"- {path}" for path in selected_files) or "- none"
    other_block = "\n".join(f"- {path}" for path in result.other_files) or "- none"
    rec_block = "\n".join(f"- {item}" for item in result.recommendations)
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
    clean_branch_name = branch_name or f"patchflow/clean-{result.branch.current_branch}"

    commit_block = "\n".join(f"- {commit.message}" for commit in selected_commits) or "- none"
    file_block = "\n".join(f"- {path}" for path in selected_files) or "- none"

    return (
        f"Planned branch: {clean_branch_name}\n\n"
        "Selected commits:\n"
        f"{commit_block}\n\n"
        "Selected files:\n"
        f"{file_block}\n\n"
        "Safe: original branch unchanged"
    )


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
