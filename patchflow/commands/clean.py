import click

from patchflow.analysis.scope import analyze_branch_scope
from patchflow.cleaning.branch_builder import (
    CleanBranchError,
    create_clean_branch,
    render_clean_summary,
)
from patchflow.utils.output import (
    render_clean_error_json,
    render_clean_preview,
    render_clean_preview_json,
    render_clean_summary_json,
)


def _resolve_cluster_selection(
    result,
    cluster_index: int | None,
    yes: bool,
    json_output: bool,
) -> int | None:
    if result.selected_cluster is None:
        raise _clean_exception("No cluster is available to clean.", code="no_cluster", json_output=json_output)

    if result.confidence != "LOW" or cluster_index is not None:
        return cluster_index

    if yes:
        raise _clean_exception(
            "Scope detection confidence is LOW. Re-run with --cluster <id> or omit --yes to choose interactively.",
            code="low_confidence",
            json_output=json_output,
        )

    selected = click.prompt(
        f"Scope detection is LOW. Choose a cluster (1-{len(result.clusters)})",
        type=click.IntRange(1, len(result.clusters)),
    )
    return selected


def _clean_exception(message: str, *, code: str, json_output: bool) -> click.ClickException:
    rendered = render_clean_error_json(message, code=code) if json_output else message
    return click.ClickException(rendered)


@click.command(name="clean")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--dry-run", is_flag=True, help="Show the clean plan without creating a branch.")
@click.option(
    "--switch",
    "switch_to_clean",
    is_flag=True,
    help="Leave the working tree on the clean branch after creation.",
)
@click.option("--branch-name", type=str, default=None, help="Override the generated clean branch name.")
@click.option(
    "--cluster",
    "cluster_index",
    type=int,
    default=None,
    help="Use a specific cluster by 1-based index.",
)
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def clean_command(
    yes: bool,
    dry_run: bool,
    switch_to_clean: bool,
    branch_name: str | None,
    cluster_index: int | None,
    json_output: bool,
) -> None:
    """Create a clean branch from the selected cluster."""
    try:
        result = analyze_branch_scope(cluster_index=cluster_index)
    except ValueError as exc:
        raise _clean_exception(str(exc), code="invalid_cluster", json_output=json_output) from exc

    resolved_cluster_index = _resolve_cluster_selection(result, cluster_index, yes, json_output)
    if resolved_cluster_index != cluster_index:
        result = analyze_branch_scope(cluster_index=resolved_cluster_index)

    if dry_run or not json_output:
        click.echo(
            render_clean_preview_json(result, branch_name)
            if json_output
            else render_clean_preview(result, branch_name)
        )

    if dry_run:
        return

    if not yes and not click.confirm("Proceed?"):
        raise click.Abort()

    try:
        summary = create_clean_branch(
            result,
            branch_name=branch_name,
            switch=switch_to_clean,
        )
    except CleanBranchError as exc:
        message = str(exc)
        code = (
            "uncommitted_only"
            if "uncommitted-only changes" in message
            else "branch_exists"
            if "already exists" in message
            else "git_failure"
        )
        raise _clean_exception(message, code=code, json_output=json_output) from exc

    click.echo(render_clean_summary_json(summary) if json_output else render_clean_summary(summary))
