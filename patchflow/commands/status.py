import click

from patchflow.github.pr_status import get_pr_status
from patchflow.utils.output import render_status


@click.command(name="status")
@click.option("--pr", "pr_ref", type=str, default=None, help="PR number or URL.")
def status_command(pr_ref: str | None) -> None:
    """Summarize simple blockers for an existing PR."""
    result = get_pr_status(pr_ref=pr_ref)
    click.echo(render_status(result))
