from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class CommitInfo:
    full_hash: str
    short_hash: str
    committed_at: datetime
    author: str
    message: str


@dataclass(frozen=True)
class UpdateInfo:
    local_commit: str
    remote_commit: str
    commits: tuple[CommitInfo, ...]

    @property
    def has_updates(self) -> bool:
        return self.local_commit != self.remote_commit

    @property
    def commit_count(self) -> int:
        return len(self.commits)


@dataclass(frozen=True)
class BackupResult:
    source_path: Path
    backup_path: Path
    created_at: datetime


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    return_code: int
    output: str

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0


class UpdaterError(Exception):
    """Base exception shown to users as an understandable updater failure."""


class GitError(UpdaterError):
    """Raised when a git operation fails."""


class BackupError(UpdaterError):
    """Raised when the SQLite backup cannot be created."""


class MigrationError(UpdaterError):
    """Raised when Django migrations fail."""


class DependencyInstallError(UpdaterError):
    """Raised when requirements installation fails."""
