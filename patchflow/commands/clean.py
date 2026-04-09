import click

from patchflow.analysis.scope import analyze_branch_scope
from patchflow.cleaning.branch_builder import create_clean_branch
from patchflow.utils.output import render_clean_preview


@click.command(name="clean")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
@click.option("--dry-run", is_flag=True, help="Show the clean plan without creating a branch.")
@click.option("--branch-name", type=str, default=None, help="Override the generated clean branch name.")
def clean_command(yes: bool, dry_run: bool, branch_name: str | None) -> None:
    """Create a clean branch from the selected cluster."""
    result = analyze_branch_scope()
    click.echo(render_clean_preview(result, branch_name))

    if dry_run:
        return

    if not yes and not click.confirm("Proceed?"):
        raise click.Abort()

    summary = create_clean_branch(result, branch_name=branch_name)
    click.echo(summary)
