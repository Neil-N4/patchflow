from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from patchflow.git.repo import get_branch_context


class PRStatusError(RuntimeError):
    """Raised when Patchflow cannot fetch PR status."""


@dataclass
class PRStatusResult:
    status: str
    checks: list[str]
    reviews: list[str]
    branch: list[str]
    conflicts: list[str]
    recommendation: str


@dataclass
class RepoRef:
    owner: str
    repo: str


@dataclass
class PullRequestRef:
    repo: RepoRef
    number: int


def _git(*args: str) -> str:
    import subprocess

    completed = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _github_request(path: str) -> object:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "patchflow",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        f"https://api.github.com{path}",
        headers=headers,
    )
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PRStatusError(f"GitHub API error {exc.code}: {detail}") from exc
    except URLError as exc:
        raise PRStatusError(f"Unable to reach GitHub API: {exc.reason}") from exc


def _repo_ref_from_remote() -> RepoRef:
    remote_url = _git("remote", "get-url", "origin")
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]

    if remote_url.startswith("git@github.com:"):
        slug = remote_url.split(":", maxsplit=1)[1]
    else:
        parsed = urlparse(remote_url)
        if parsed.netloc != "github.com":
            raise PRStatusError("Origin remote is not a GitHub repository.")
        slug = parsed.path.lstrip("/")

    parts = slug.split("/")
    if len(parts) != 2:
        raise PRStatusError("Could not determine GitHub owner/repo from origin remote.")
    return RepoRef(owner=parts[0], repo=parts[1])


def _parse_pr_ref(pr_ref: str) -> PullRequestRef:
    if pr_ref.isdigit():
        repo = _repo_ref_from_remote()
        return PullRequestRef(repo=repo, number=int(pr_ref))

    parsed = urlparse(pr_ref)
    if parsed.netloc != "github.com":
        raise PRStatusError("PR URL must be a github.com URL.")
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 4 or parts[2] != "pull":
        raise PRStatusError("PR URL must look like https://github.com/<owner>/<repo>/pull/<number>.")
    owner, repo, _, number = parts[:4]
    if not number.isdigit():
        raise PRStatusError("PR number in URL is invalid.")
    return PullRequestRef(repo=RepoRef(owner=owner, repo=repo), number=int(number))


def _infer_pr_ref() -> PullRequestRef:
    repo = _repo_ref_from_remote()
    branch = get_branch_context().current_branch
    pulls = _github_request(
        f"/repos/{repo.owner}/{repo.repo}/pulls?state=open&head={repo.owner}:{branch}"
    )
    if not pulls:
        raise PRStatusError(
            "No open pull request found for the current branch. Pass --pr <number|url>."
        )
    pr_number = pulls[0]["number"]
    return PullRequestRef(repo=repo, number=pr_number)


def _resolve_pr_ref(pr_ref: str | None) -> PullRequestRef:
    if pr_ref:
        return _parse_pr_ref(pr_ref)
    return _infer_pr_ref()


def _review_summary(pr: dict[str, object], reviews: list[dict[str, object]]) -> list[str]:
    latest_by_user: dict[str, str] = {}
    for review in reviews:
        user = review.get("user") or {}
        login = user.get("login")
        state = review.get("state")
        if isinstance(login, str) and isinstance(state, str):
            latest_by_user[login] = state

    if not latest_by_user:
        return ["no reviews yet"]

    approvals = sorted(login for login, state in latest_by_user.items() if state == "APPROVED")
    pending = sorted(login for login, state in latest_by_user.items() if state in {"COMMENTED", "CHANGES_REQUESTED"})

    lines: list[str] = []
    if approvals:
        lines.append("approved by: " + ", ".join(approvals))
    if pending:
        lines.append("active review state from: " + ", ".join(pending))
    requested_reviewers = [
        reviewer.get("login")
        for reviewer in pr.get("requested_reviewers", [])
        if reviewer.get("login")
    ]
    requested_teams = [
        team.get("slug")
        for team in pr.get("requested_teams", [])
        if team.get("slug")
    ]
    if requested_reviewers:
        lines.append("requested reviewers: " + ", ".join(sorted(requested_reviewers)))
    if requested_teams:
        lines.append("requested teams: " + ", ".join(sorted(requested_teams)))
    return lines or ["no actionable review state"]


def _check_summary(check_runs: list[dict[str, object]], combined_state: str) -> list[str]:
    lines: list[str] = []
    if check_runs:
        for run in check_runs[:5]:
            name = run.get("name", "unnamed check")
            status = run.get("status", "unknown")
            conclusion = run.get("conclusion")
            suffix = f" ({conclusion})" if conclusion else ""
            lines.append(f"{name}: {status}{suffix}")
    if not check_runs or combined_state not in {"success", "unknown"}:
        lines.append(f"combined status: {combined_state}")
    return lines


def _branch_summary(pr: dict[str, object], compare: dict[str, object]) -> list[str]:
    lines = []
    behind_by = compare.get("behind_by", 0)
    ahead_by = compare.get("ahead_by", 0)
    lines.append(f"behind base by {behind_by} commits")
    lines.append(f"ahead of base by {ahead_by} commits")
    mergeable_state = pr.get("mergeable_state")
    if mergeable_state:
        lines.append(f"mergeable_state: {mergeable_state}")
    return lines


def _conflict_summary(pr: dict[str, object]) -> list[str]:
    mergeable = pr.get("mergeable")
    if mergeable is False:
        return ["merge conflicts detected or GitHub cannot merge cleanly"]
    if mergeable is None:
        return ["mergeability not yet computed by GitHub"]
    return ["none"]


def _recommendation(pr: dict[str, object], compare: dict[str, object], reviews: list[dict[str, object]], check_runs: list[dict[str, object]], combined_state: str) -> str:
    if compare.get("behind_by", 0) > 0:
        return "update branch"

    if any(review.get("state") == "CHANGES_REQUESTED" for review in reviews):
        return "respond/comment"

    if any(run.get("conclusion") in {"failure", "timed_out", "cancelled"} for run in check_runs):
        return "respond/comment"

    if combined_state == "failure":
        return "respond/comment"

    if pr.get("mergeable") is False:
        return "respond/comment"

    return "wait"


def get_pr_status(pr_ref: str | None) -> PRStatusResult:
    resolved = _resolve_pr_ref(pr_ref)
    owner = resolved.repo.owner
    repo = resolved.repo.repo
    number = resolved.number

    pr = _github_request(f"/repos/{owner}/{repo}/pulls/{number}")
    head_sha = pr["head"]["sha"]
    base_sha = pr["base"]["sha"]
    reviews = _github_request(f"/repos/{owner}/{repo}/pulls/{number}/reviews")
    combined_status = _github_request(f"/repos/{owner}/{repo}/commits/{head_sha}/status")
    check_runs_response = _github_request(
        f"/repos/{owner}/{repo}/commits/{head_sha}/check-runs"
    )
    compare = _github_request(f"/repos/{owner}/{repo}/compare/{base_sha}...{head_sha}")

    check_runs = check_runs_response.get("check_runs", [])
    combined_state = combined_status.get("state", "unknown")

    recommendation = _recommendation(
        pr=pr,
        compare=compare,
        reviews=reviews,
        check_runs=check_runs,
        combined_state=combined_state,
    )
    status = "BLOCKED" if recommendation != "wait" else "WAITING"

    return PRStatusResult(
        status=status,
        checks=_check_summary(check_runs, combined_state),
        reviews=_review_summary(pr, reviews),
        branch=_branch_summary(pr, compare),
        conflicts=_conflict_summary(pr),
        recommendation=recommendation,
    )
