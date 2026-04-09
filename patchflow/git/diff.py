from patchflow.git.repo import detect_base_branch


def list_changed_files() -> list[str]:
    base_branch = detect_base_branch()
    return [f for f in [".vscode/launch.json"] if f]
