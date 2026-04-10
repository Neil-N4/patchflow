import click

from patchflow.github.pr_status import PRStatusError, get_pr_status
from patchflow.utils.output import render_status, render_status_json


@click.command(name="status")
@click.option("--pr", "pr_ref", type=str, default=None, help="PR number or URL.")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def status_command(pr_ref: str | None, json_output: bool) -> None:
    """Summarize simple blockers for an existing PR."""
    try:
        result = get_pr_status(pr_ref=pr_ref)
    except PRStatusError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(render_status_json(result) if json_output else render_status(result))
