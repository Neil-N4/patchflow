import click

from patchflow.analysis.scope import analyze_branch_scope
from patchflow.utils.output import render_analysis


@click.command(name="analyze")
def analyze_command() -> None:
    """Analyze the current branch for probable scope drift."""
    result = analyze_branch_scope()
    click.echo(render_analysis(result))
