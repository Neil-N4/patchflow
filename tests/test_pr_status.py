from __future__ import annotations

import unittest

from patchflow.github.pr_status import (
    _check_summary,
    _conflict_summary,
    _parse_pr_ref,
    _recommendation,
    _review_summary,
)


class PRStatusTests(unittest.TestCase):
    def test_parse_pr_ref_from_url(self) -> None:
        ref = _parse_pr_ref("https://github.com/google-gemini/gemini-cli/pull/22894")

        self.assertEqual(ref.repo.owner, "google-gemini")
        self.assertEqual(ref.repo.repo, "gemini-cli")
        self.assertEqual(ref.number, 22894)

    def test_review_summary_includes_requested_reviewers_and_approvals(self) -> None:
        pr = {
            "requested_reviewers": [{"login": "alice"}],
            "requested_teams": [{"slug": "cli-maintainers"}],
        }
        reviews = [
            {"user": {"login": "bob"}, "state": "APPROVED"},
            {"user": {"login": "carol"}, "state": "CHANGES_REQUESTED"},
        ]

        summary = _review_summary(pr, reviews)

        self.assertIn("approved by: bob", summary)
        self.assertIn("active review state from: carol", summary)
        self.assertIn("requested reviewers: alice", summary)
        self.assertIn("requested teams: cli-maintainers", summary)

    def test_check_summary_falls_back_to_combined_state(self) -> None:
        summary = _check_summary([], "pending")

        self.assertEqual(summary, ["combined status: pending"])

    def test_recommendation_prefers_update_branch(self) -> None:
        recommendation = _recommendation(
            pr={"mergeable": True},
            compare={"behind_by": 3},
            reviews=[],
            check_runs=[],
            combined_state="success",
        )

        self.assertEqual(recommendation, "update branch")

    def test_recommendation_responds_on_requested_changes(self) -> None:
        recommendation = _recommendation(
            pr={"mergeable": True},
            compare={"behind_by": 0},
            reviews=[{"state": "CHANGES_REQUESTED"}],
            check_runs=[],
            combined_state="success",
        )

        self.assertEqual(recommendation, "respond/comment")

    def test_conflict_summary_detects_conflicts(self) -> None:
        summary = _conflict_summary({"mergeable": False})

        self.assertEqual(summary, ["merge conflicts detected or GitHub cannot merge cleanly"])


if __name__ == "__main__":
    unittest.main()
