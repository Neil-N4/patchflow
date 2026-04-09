from dataclasses import dataclass


@dataclass
class CommitRecord:
    sha: str
    message: str
    files: list[str]
