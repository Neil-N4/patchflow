from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from patchflow.commands.clean import clean_command
from patchflow.commands.analyze import analyze_command
from patchflow.commands.status import status_command
from patchflow.github.pr_status import PRStatusResult


class JsonOutputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def make_repo(self) -> Path:
        repo = Path(tempfile.mkdtemp(prefix="patchflow-json-"))
        os.system(f"cd {repo} && git init -b main >/dev/null 2>&1")
        os.system(f"cd {repo} && git config user.name 'Patchflow Test'")
        os.system(f"cd {repo} && git config user.email 'patchflow@example.com'")
        return repo

    def test_analyze_json_output_shape(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        os.system(f"cd {repo} && git add app.txt && git commit -m 'base commit' >/dev/null 2>&1")
        os.system(f"cd {repo} && git switch -c feature/json >/dev/null 2>&1")
        (repo / "app.txt").write_text("base\nfeature\n")
        os.system(f"cd {repo} && git add app.txt && git commit -m 'feat: update app' >/dev/null 2>&1")

        cwd = Path.cwd()
        try:
            os.chdir(repo)
            result = self.runner.invoke(analyze_command, ["--json"])
        finally:
            os.chdir(cwd)

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["branch"]["current"], "feature/json")
        self.assertEqual(payload["branch"]["base"], "main")
        self.assertEqual(payload["status"], "CLEAN")
        self.assertEqual(payload["selected_cluster_index"], 1)
        self.assertEqual(len(payload["clusters"]), 1)
        self.assertIn("app.txt", payload["changed_files"])

    def test_status_json_output_shape(self) -> None:
        fake_result = PRStatusResult(
            status="WAITING",
            checks=["combined status: pending"],
            reviews=["requested teams: core"],
            branch=["behind base by 0 commits"],
            conflicts=["none"],
            recommendation="wait",
        )

        with patch("patchflow.commands.status.get_pr_status", return_value=fake_result):
            result = self.runner.invoke(
                status_command,
                ["--pr", "123", "--json"],
            )

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["status"], "WAITING")
        self.assertEqual(payload["recommendation"], "wait")
        self.assertEqual(payload["checks"], ["combined status: pending"])
        self.assertEqual(payload["reviews"], ["requested teams: core"])

    def test_clean_json_dry_run_shape(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        os.system(f"cd {repo} && git add app.txt && git commit -m 'base commit' >/dev/null 2>&1")
        os.system(f"cd {repo} && git switch -c feature/json-clean >/dev/null 2>&1")
        (repo / "app.txt").write_text("base\nfeature\n")
        os.system(f"cd {repo} && git add app.txt && git commit -m 'feat: update app' >/dev/null 2>&1")

        cwd = Path.cwd()
        try:
            os.chdir(repo)
            result = self.runner.invoke(clean_command, ["--dry-run", "--json"])
        finally:
            os.chdir(cwd)

        self.assertEqual(result.exit_code, 0, msg=result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["branch_name"], "patchflow/clean-feature-json-clean")
        self.assertEqual(payload["selected_cluster_index"], 1)
        self.assertEqual(len(payload["selected_commits"]), 1)
        self.assertEqual(payload["selected_commits"][0]["message"], "feat: update app")
        self.assertTrue(payload["safe"])

    def test_clean_json_low_confidence_error_shape(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        os.system(f"cd {repo} && git add app.txt && git commit -m 'base commit' >/dev/null 2>&1")
        os.system(f"cd {repo} && git switch -c feature/json-low >/dev/null 2>&1")
        (repo / "app.txt").write_text("base\nfeature\n")
        os.system(f"cd {repo} && git add app.txt && git commit -m 'feat: update app' >/dev/null 2>&1")
        (repo / "notes.md").write_text("notes\n")
        os.system(f"cd {repo} && git add notes.md && git commit -m 'docs: add notes' >/dev/null 2>&1")

        cwd = Path.cwd()
        try:
            os.chdir(repo)
            result = self.runner.invoke(clean_command, ["--yes", "--json"])
        finally:
            os.chdir(cwd)

        self.assertNotEqual(result.exit_code, 0)
        payload = json.loads(result.output.split("Error: ", maxsplit=1)[1])
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "low_confidence")

    def test_clean_json_uncommitted_only_error_shape(self) -> None:
        repo = self.make_repo()
        (repo / "scratch.txt").write_text("draft\n")

        cwd = Path.cwd()
        try:
            os.chdir(repo)
            result = self.runner.invoke(clean_command, ["--yes", "--json"])
        finally:
            os.chdir(cwd)

        self.assertNotEqual(result.exit_code, 0)
        payload = json.loads(result.output.split("Error: ", maxsplit=1)[1])
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], "uncommitted_only")


if __name__ == "__main__":
    unittest.main()
