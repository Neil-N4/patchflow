import unittest

from patchflow.analysis.clustering import CommitCluster
from patchflow.analysis.scope import ScopeAnalysisResult
from patchflow.cleaning.branch_builder import default_clean_branch_name
from patchflow.git.commits import CommitRecord
from patchflow.github.pr_status import PRStatusResult
from patchflow.git.repo import BranchContext
from patchflow.tui.presenter import (
    branch_summary_text,
    cluster_label,
    detail_text,
    pr_status_text,
)


def _result() -> ScopeAnalysisResult:
    cluster = CommitCluster(
        label="cluster-1",
        commits=[CommitRecord(sha="abc123", message="feat: update app", files=["src/app.py"])],
        files=["src/app.py"],
        score=9.5,
        confidence="HIGH",
    )
    return ScopeAnalysisResult(
        branch=BranchContext(
            current_branch="feature/demo",
            base_branch="main",
            ahead_by=2,
            behind_by=0,
            has_uncommitted_changes=False,
        ),
        status="DIRTY",
        confidence="HIGH",
        clusters=[cluster],
        selected_cluster=cluster,
        selected_cluster_index=0,
        changed_files=["src/app.py"],
        worktree_files=[],
        other_files=[],
        recommendations=["clean branch"],
    )


class TuiPresenterTests(unittest.TestCase):
    def test_branch_summary_text_includes_core_fields(self) -> None:
        text = branch_summary_text(_result())
        self.assertIn("Branch: feature/demo", text)
        self.assertIn("Base: main", text)
        self.assertIn("Confidence: HIGH", text)

    def test_cluster_label_marks_selected_cluster(self) -> None:
        text = cluster_label(_result(), 0)
        self.assertIn("[1] cluster-1 *", text)
        self.assertIn("score=9.50", text)

    def test_detail_text_includes_planned_branch_name(self) -> None:
        result = _result()
        text = detail_text(result, None)
        self.assertIn(default_clean_branch_name(result.branch.current_branch), text)
        self.assertIn("Selected commits:", text)
        self.assertIn("Switch after clean: off", text)

    def test_detail_text_marks_switch_mode(self) -> None:
        text = detail_text(_result(), None, switch_to_clean=True)
        self.assertIn("Switch after clean: on", text)

    def test_pr_status_text_renders_sections(self) -> None:
        text = pr_status_text(
            PRStatusResult(
                status="WAITING",
                checks=["combined status: pending"],
                reviews=["requested teams: core"],
                branch=["behind base by 0 commits"],
                conflicts=["none"],
                recommendation="wait",
            )
        )
        self.assertIn("PR Status: WAITING", text)
        self.assertIn("Checks:", text)
        self.assertIn("requested teams: core", text)

    def test_pr_status_text_renders_error(self) -> None:
        text = pr_status_text(None, error="No open pull request found")
        self.assertIn("PR status unavailable", text)
        self.assertIn("No open pull request found", text)


if __name__ == "__main__":
    unittest.main()
