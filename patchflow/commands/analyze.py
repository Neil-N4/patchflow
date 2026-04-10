import click

from patchflow.analysis.scope import analyze_branch_scope
from patchflow.utils.output import render_analysis


@click.command(name="analyze")
@click.option(
    "--cluster",
    "cluster_index",
    type=int,
    default=None,
    help="Select a specific cluster by 1-based index.",
)
def analyze_command(cluster_index: int | None) -> None:
    """Analyze the current branch for probable scope drift."""
    try:
        result = analyze_branch_scope(cluster_index=cluster_index)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(render_analysis(result))
