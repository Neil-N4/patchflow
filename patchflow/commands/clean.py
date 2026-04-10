import click

from patchflow.analysis.scope import analyze_branch_scope
from patchflow.cleaning.branch_builder import (
    CleanBranchError,
    create_clean_branch,
    render_clean_summary,
)
from patchflow.utils.output import render_clean_preview


def _resolve_cluster_selection(
    result,
    cluster_index: int | None,
    yes: bool,
) -> int | None:
    if result.selected_cluster is None:
        raise click.ClickException("No cluster is available to clean.")

    if result.confidence != "LOW" or cluster_index is not None:
        return cluster_index

    if yes:
        raise click.ClickException(
            "Scope detection confidence is LOW. Re-run with --cluster <id> or omit --yes to choose interactively."
        )

    selected = click.prompt(
        f"Scope detection is LOW. Choose a cluster (1-{len(result.clusters)})",
        type=click.IntRange(1, len(result.clusters)),
    )
    return selected


@click.command(name="clean")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--dry-run", is_flag=True, help="Show the clean plan without creating a branch.")
@click.option("--branch-name", type=str, default=None, help="Override the generated clean branch name.")
@click.option(
    "--cluster",
    "cluster_index",
    type=int,
    default=None,
    help="Use a specific cluster by 1-based index.",
)
def clean_command(
    yes: bool,
    dry_run: bool,
    branch_name: str | None,
    cluster_index: int | None,
) -> None:
    """Create a clean branch from the selected cluster."""
    try:
        result = analyze_branch_scope(cluster_index=cluster_index)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    resolved_cluster_index = _resolve_cluster_selection(result, cluster_index, yes)
    if resolved_cluster_index != cluster_index:
        result = analyze_branch_scope(cluster_index=resolved_cluster_index)

    click.echo(render_clean_preview(result, branch_name))

    if dry_run:
        return

    if not yes and not click.confirm("Proceed?"):
        raise click.Abort()

    try:
        summary = create_clean_branch(result, branch_name=branch_name)
    except CleanBranchError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(render_clean_summary(summary))
