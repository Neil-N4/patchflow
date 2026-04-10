from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.metadata
import os
import shutil
import subprocess
import sys

from patchflow.git.repo import BranchContext, get_branch_context


@dataclass
class DoctorCheck:
    name: str
    status: str
    summary: str


@dataclass
class DoctorResult:
    overall_status: str
    patchflow_version: str
    python_version: str
    checks: list[DoctorCheck]
    branch: dict[str, object] | None


def _command_version(command: str, *args: str) -> str | None:
    try:
      completed = subprocess.run(
          [command, *args],
          check=True,
          capture_output=True,
          text=True,
      )
    except (FileNotFoundError, subprocess.CalledProcessError):
      return None
    return completed.stdout.strip() or completed.stderr.strip() or None


def _branch_payload(branch: BranchContext) -> dict[str, object]:
    return {
        "current": branch.current_branch,
        "base": branch.base_branch,
        "ahead_by": branch.ahead_by,
        "behind_by": branch.behind_by,
        "has_uncommitted_changes": branch.has_uncommitted_changes,
    }


def run_doctor() -> DoctorResult:
    checks: list[DoctorCheck] = []
    branch_context: BranchContext | None = None
    overall = "OK"

    git_path = shutil.which("git")
    if git_path:
        git_version = _command_version("git", "--version") or "git is installed"
        checks.append(DoctorCheck(name="git", status="OK", summary=git_version))
    else:
        checks.append(DoctorCheck(name="git", status="FAIL", summary="git is not installed or not on PATH."))
        overall = "FAIL"

    inside_worktree = False
    if git_path:
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                check=True,
                capture_output=True,
                text=True,
            )
            inside_worktree = completed.stdout.strip() == "true"
        except subprocess.CalledProcessError:
            inside_worktree = False

    if inside_worktree:
        checks.append(DoctorCheck(name="workspace", status="OK", summary="Current directory is inside a git worktree."))
        try:
            branch_context = get_branch_context()
            checks.append(
                DoctorCheck(
                    name="branch",
                    status="OK",
                    summary=(
                        f"{branch_context.current_branch} against {branch_context.base_branch} "
                        f"(ahead {branch_context.ahead_by}, behind {branch_context.behind_by})"
                    ),
                )
            )
        except subprocess.CalledProcessError as exc:
            checks.append(
                DoctorCheck(
                    name="branch",
                    status="WARN",
                    summary=f"Patchflow could not inspect branch context: {exc}",
                )
            )
            if overall == "OK":
                overall = "WARN"
    else:
        checks.append(
            DoctorCheck(
                name="workspace",
                status="WARN",
                summary="Current directory is not inside a git worktree. Analyze, clean, and status will not work here.",
            )
        )
        if overall == "OK":
            overall = "WARN"

    token_present = bool(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    gh_version = _command_version("gh", "--version")
    if token_present:
        checks.append(DoctorCheck(name="github_auth", status="OK", summary="GitHub token detected in environment."))
    elif gh_version:
        checks.append(
            DoctorCheck(
                name="github_auth",
                status="WARN",
                summary="GitHub token not detected. PR status may work only for public repos unless gh auth is already configured.",
            )
        )
        if overall == "OK":
            overall = "WARN"
    else:
        checks.append(
            DoctorCheck(
                name="github_auth",
                status="WARN",
                summary="No GitHub token detected and gh is unavailable. PR status will be limited to public repos only.",
            )
        )
        if overall == "OK":
            overall = "WARN"

    textual_version = importlib.metadata.version("textual")
    checks.append(
        DoctorCheck(
            name="tui",
            status="OK",
            summary=f"textual {textual_version}",
        )
    )

    return DoctorResult(
        overall_status=overall,
        patchflow_version=importlib.metadata.version("patchflow"),
        python_version=sys.version.split()[0],
        checks=checks,
        branch=_branch_payload(branch_context) if branch_context else None,
    )


def doctor_to_dict(result: DoctorResult) -> dict[str, object]:
    return {
        "overall_status": result.overall_status,
        "patchflow_version": result.patchflow_version,
        "python_version": result.python_version,
        "checks": [asdict(check) for check in result.checks],
        "branch": result.branch,
    }
