import json

import click

from patchflow.doctor import doctor_to_dict, run_doctor


def render_doctor(result) -> str:
    checks_block = "\n".join(
        f"- [{check.status}] {check.name}: {check.summary}" for check in result.checks
    )
    branch_block = (
        "Unavailable"
        if result.branch is None
        else (
            f"{result.branch['current']} against {result.branch['base']} "
            f"(ahead {result.branch['ahead_by']}, behind {result.branch['behind_by']})"
        )
    )
    return (
        f"Patchflow Doctor: {result.overall_status}\n\n"
        f"Patchflow version: {result.patchflow_version}\n"
        f"Python version: {result.python_version}\n"
        f"Branch context: {branch_block}\n\n"
        "Checks:\n"
        f"{checks_block}"
    )


@click.command(name="doctor")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def doctor_command(json_output: bool) -> None:
    """Inspect local Patchflow environment and repository health."""
    result = run_doctor()
    click.echo(
        json.dumps(doctor_to_dict(result), indent=2, sort_keys=True)
        if json_output
        else render_doctor(result)
    )
