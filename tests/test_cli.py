from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(
    cmd: list[str],
    cwd: Path,
    *,
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    repo_path = str(REPO_ROOT)
    env["PYTHONPATH"] = (
        f"{repo_path}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else repo_path
    )
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        env=env,
        input=input_text,
    )


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd, check=check)


class PatchflowCliTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="patchflow-test-"))
        git(temp_dir, "init", "-b", "main")
        git(temp_dir, "config", "user.name", "Patchflow Test")
        git(temp_dir, "config", "user.email", "patchflow@example.com")
        return temp_dir

    def test_analyze_reports_multiple_clusters(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "base commit")
        git(repo, "switch", "-c", "feature/test-clean")
        (repo / "app.txt").write_text("base\nfeature change\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "feat: update app")
        (repo / "notes.md").write_text("notes\n")
        git(repo, "add", "notes.md")
        git(repo, "commit", "-m", "docs: add notes")

        result = run(["python3", "-m", "patchflow.cli", "analyze"], repo)

        self.assertIn("Status: DIRTY", result.stdout)
        self.assertIn("Confidence: LOW", result.stdout)
        self.assertIn("Clusters:", result.stdout)
        self.assertIn("[1]", result.stdout)
        self.assertIn("[2]", result.stdout)

    def test_clean_requires_explicit_cluster_when_low_confidence(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "base commit")
        git(repo, "switch", "-c", "feature/test-clean")
        (repo / "app.txt").write_text("base\nfeature change\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "feat: update app")
        (repo / "notes.md").write_text("notes\n")
        git(repo, "add", "notes.md")
        git(repo, "commit", "-m", "docs: add notes")

        result = run(
            ["python3", "-m", "patchflow.cli", "clean", "--yes"],
            repo,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Scope detection confidence is LOW", result.stderr)

    def test_clean_creates_selected_cluster_branch(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "base commit")
        git(repo, "switch", "-c", "feature/test-clean")
        (repo / "app.txt").write_text("base\nfeature change\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "feat: update app")
        (repo / "notes.md").write_text("notes\n")
        git(repo, "add", "notes.md")
        git(repo, "commit", "-m", "docs: add notes")

        result = run(
            [
                "python3",
                "-m",
                "patchflow.cli",
                "clean",
                "--cluster",
                "2",
                "--branch-name",
                "patchflow/clean-test",
                "--yes",
            ],
            repo,
        )

        current_branch = git(repo, "branch", "--show-current").stdout.strip()
        clean_diff = git(repo, "diff", "--stat", "main..patchflow/clean-test").stdout

        self.assertEqual(current_branch, "feature/test-clean")
        self.assertIn("Created: patchflow/clean-test", result.stdout)
        self.assertIn("app.txt", clean_diff)
        self.assertNotIn("notes.md", clean_diff)

    def test_clean_interactively_selects_cluster_when_confidence_is_low(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "base commit")
        git(repo, "switch", "-c", "feature/test-clean")
        (repo / "app.txt").write_text("base\nfeature change\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "feat: update app")
        (repo / "notes.md").write_text("notes\n")
        git(repo, "add", "notes.md")
        git(repo, "commit", "-m", "docs: add notes")

        result = run(
            [
                "python3",
                "-m",
                "patchflow.cli",
                "clean",
                "--branch-name",
                "patchflow/clean-interactive-test",
            ],
            repo,
            input_text="2\ny\n",
        )

        current_branch = git(repo, "branch", "--show-current").stdout.strip()
        clean_diff = git(repo, "diff", "--stat", "main..patchflow/clean-interactive-test").stdout

        self.assertEqual(current_branch, "feature/test-clean")
        self.assertIn("Created: patchflow/clean-interactive-test", result.stdout)
        self.assertIn("app.txt", clean_diff)
        self.assertNotIn("notes.md", clean_diff)

    def test_clean_switches_to_clean_branch_when_requested(self) -> None:
        repo = self.make_repo()
        (repo / "app.txt").write_text("base\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "base commit")
        git(repo, "switch", "-c", "feature/test-switch")
        (repo / "app.txt").write_text("base\nfeature change\n")
        git(repo, "add", "app.txt")
        git(repo, "commit", "-m", "feat: update app")
        (repo / "notes.md").write_text("notes\n")
        git(repo, "add", "notes.md")
        git(repo, "commit", "-m", "docs: add notes")

        result = run(
            [
                "python3",
                "-m",
                "patchflow.cli",
                "clean",
                "--cluster",
                "2",
                "--branch-name",
                "patchflow/clean-switch-test",
                "--switch",
                "--yes",
            ],
            repo,
        )

        current_branch = git(repo, "branch", "--show-current").stdout.strip()

        self.assertEqual(current_branch, "patchflow/clean-switch-test")
        self.assertIn("Current branch: patchflow/clean-switch-test", result.stdout)

    def test_analyze_prefers_stacked_feature_commits_over_single_noise_commit(self) -> None:
        repo = self.make_repo()
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("print('base')\n")
        git(repo, "add", "src/app.py")
        git(repo, "commit", "-m", "base commit")
        git(repo, "switch", "-c", "feature/stacked")

        (repo / "src" / "app.py").write_text("print('base')\nprint('step1')\n")
        git(repo, "add", "src/app.py")
        git(repo, "commit", "-m", "feat: add first app step")

        (repo / "src" / "utils.py").write_text("def helper():\n    return 'ok'\n")
        git(repo, "add", "src/utils.py")
        git(repo, "commit", "-m", "feat: add helper for app")

        (repo / "README.md").write_text("temporary notes\n")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "docs: temporary readme note")

        result = run(["python3", "-m", "patchflow.cli", "analyze"], repo)

        self.assertIn("Confidence: HIGH", result.stdout)
        self.assertIn("feat: add first app step", result.stdout)
        self.assertIn("feat: add helper for app", result.stdout)
        self.assertIn("README.md", result.stdout)
        self.assertIn("Other changes:\n- README.md", result.stdout)

    def test_analyze_keeps_uncommitted_changes_out_of_primary_when_branch_commits_exist(self) -> None:
        repo = self.make_repo()
        (repo / "src").mkdir()
        (repo / "src" / "app.py").write_text("print('base')\n")
        git(repo, "add", "src/app.py")
        git(repo, "commit", "-m", "base commit")
        git(repo, "switch", "-c", "feature/mixed")

        (repo / "src" / "app.py").write_text("print('base')\nprint('feature')\n")
        git(repo, "add", "src/app.py")
        git(repo, "commit", "-m", "feat: update app")

        (repo / "scratch.txt").write_text("debug scratch\n")

        result = run(["python3", "-m", "patchflow.cli", "analyze"], repo)

        self.assertIn("Confidence: HIGH", result.stdout)
        self.assertIn("feat: update app", result.stdout)
        self.assertIn("Other changes:\n- scratch.txt", result.stdout)
        self.assertNotIn("commit: uncommitted changes\n  file: scratch.txt", result.stdout)


if __name__ == "__main__":
    unittest.main()
