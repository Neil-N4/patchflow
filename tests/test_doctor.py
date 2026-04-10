import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class DoctorCommandTests(unittest.TestCase):
    def test_doctor_json_output_shape_in_repo(self) -> None:
        completed = subprocess.run(
            ["python3", "-m", "patchflow.cli", "doctor", "--json"],
            cwd=Path(__file__).resolve().parent.parent,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema_version"], "1")
        self.assertIn(payload["overall_status"], {"OK", "WARN", "FAIL"})
        self.assertIn("patchflow_version", payload)
        self.assertIn("python_version", payload)
        self.assertIsInstance(payload["checks"], list)
        self.assertIsInstance(payload["branch"], dict)

    def test_doctor_warns_outside_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env.pop("GITHUB_TOKEN", None)
            env.pop("GH_TOKEN", None)
            completed = subprocess.run(
                ["python3", "-m", "patchflow.cli", "doctor", "--json"],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["schema_version"], "1")
        self.assertEqual(payload["branch"], None)
        self.assertIn(payload["overall_status"], {"WARN", "FAIL"})
        workspace_checks = [check for check in payload["checks"] if check["name"] == "workspace"]
        self.assertEqual(len(workspace_checks), 1)
        self.assertEqual(workspace_checks[0]["status"], "WARN")
