from patchflow.git.repo import _run_git, detect_base_branch


def _split_lines(output: str) -> list[str]:
    return [line for line in output.splitlines() if line]


def list_changed_files() -> list[str]:
    base_branch = detect_base_branch()
    files: set[str] = set()

    try:
        merge_base = _run_git("merge-base", "HEAD", base_branch)
        files.update(_split_lines(_run_git("diff", "--name-only", f"{merge_base}..HEAD")))
    except Exception:
        pass

    files.update(_split_lines(_run_git("diff", "--name-only")))
    files.update(_split_lines(_run_git("diff", "--name-only", "--cached")))
    return sorted(files)


def list_worktree_files() -> list[str]:
    files = set(_split_lines(_run_git("diff", "--name-only")))
    files.update(_split_lines(_run_git("diff", "--name-only", "--cached")))
    return sorted(files)
