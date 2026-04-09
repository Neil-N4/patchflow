from dataclasses import dataclass


@dataclass
class PRStatusResult:
    status: str
    checks: list[str]
    reviews: list[str]
    branch: list[str]
    conflicts: list[str]
    recommendation: str


def get_pr_status(pr_ref: str | None) -> PRStatusResult:
    ref_note = pr_ref or "auto-detect not implemented"
    return PRStatusResult(
        status="BLOCKED",
        checks=["CI: unavailable in V1 scaffold"],
        reviews=["PR ref: " + ref_note],
        branch=["branch sync status not implemented"],
        conflicts=["none"],
        recommendation="wait",
    )
