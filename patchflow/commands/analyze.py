import click

from patchflow.analysis.scope import analyze_branch_scope
from patchflow.utils.output import render_analysis, render_analysis_json


@click.command(name="analyze")
@click.option(
    "--cluster",
    "cluster_index",
    type=int,
    default=None,
    help="Select a specific cluster by 1-based index.",
)
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def analyze_command(cluster_index: int | None, json_output: bool) -> None:
    """Analyze the current branch for probable scope drift."""
    try:
        result = analyze_branch_scope(cluster_index=cluster_index)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(render_analysis_json(result) if json_output else render_analysis(result))
