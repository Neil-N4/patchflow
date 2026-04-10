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


if __name__ == "__main__":
    unittest.main()
