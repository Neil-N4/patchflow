import click


@click.command(name="tui")
@click.option(
    "--branch-name",
    type=str,
    default=None,
    help="Override the generated clean branch name used by the TUI clean action.",
)
def tui_command(branch_name: str | None) -> None:
    """Launch the Patchflow terminal UI."""
    try:
        from patchflow.tui.app import run_tui
    except ImportError as exc:
        raise click.ClickException(
            "The TUI requires the 'textual' dependency. Reinstall Patchflow with its current dependencies."
        ) from exc

    run_tui(branch_name=branch_name)
