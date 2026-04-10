import click

from patchflow.commands.analyze import analyze_command
from patchflow.commands.clean import clean_command
from patchflow.commands.status import status_command
from patchflow.commands.tui import tui_command


@click.group()
def main() -> None:
    """Patchflow CLI."""


main.add_command(analyze_command)
main.add_command(clean_command)
main.add_command(status_command)
main.add_command(tui_command)


if __name__ == "__main__":
    main()
