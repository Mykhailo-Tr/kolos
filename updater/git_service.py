from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable

from .config import UpdaterConfig
from .models import CommitInfo, GitError, UpdateInfo


LogCallback = Callable[[str], None]


class GitService:
    def __init__(self, config: UpdaterConfig) -> None:
        self.config = config

    def check_for_updates(self, log: LogCallback | None = None) -> UpdateInfo:
        self.fetch(log)
        local_commit = self.get_commit("HEAD")
        remote_commit = self.get_commit(self.config.remote_branch)
        commits = self.get_new_commits(self.config.remote_branch)
        return UpdateInfo(
            local_commit=local_commit,
            remote_commit=remote_commit,
            commits=tuple(commits),
        )

    def fetch(self, log: LogCallback | None = None) -> None:
        self._run_git(("fetch", self.config.remote_name), log=log)

    def reset_to_remote(self, log: LogCallback | None = None) -> None:
        self._run_git(("fetch", self.config.remote_name), log=log)
        self._run_git(("reset", "--hard", self.config.remote_branch), log=log)

    def get_commit(self, revision: str) -> str:
        result = self._run_git(("rev-parse", revision))
        return result.strip()

    def get_short_commit(self, revision: str = "HEAD") -> str:
        result = self._run_git(("rev-parse", "--short", revision))
        return result.strip()

    def get_new_commits(self, remote_branch: str) -> list[CommitInfo]:
        output = self._run_git(
            (
                "log",
                "--date=iso-strict",
                "--pretty=format:%H%x1f%h%x1f%cI%x1f%an%x1f%s%x1e",
                f"HEAD..{remote_branch}",
            )
        )
        commits: list[CommitInfo] = []
        for raw_entry in output.strip("\x1e\n").split("\x1e"):
            if not raw_entry.strip():
                continue
            parts = raw_entry.strip().split("\x1f")
            if len(parts) != 5:
                continue
            full_hash, short_hash, committed_at, author, message = parts
            commits.append(
                CommitInfo(
                    full_hash=full_hash,
                    short_hash=short_hash,
                    committed_at=datetime.fromisoformat(committed_at),
                    author=author,
                    message=message,
                )
            )
        return commits

    def _run_git(self, args: tuple[str, ...], log: LogCallback | None = None) -> str:
        command = ("git", *args)
        if log:
            log(f"$ {' '.join(command)}")
        try:
            completed = subprocess.run(
                command,
                cwd=Path(self.config.repo_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitError("Git не знайдено. Перевірте, що Git встановлено і доступно в PATH.") from exc
        except OSError as exc:
            raise GitError(f"Не вдалося запустити Git: {exc}") from exc

        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
        if log and output:
            log(output)
        if completed.returncode != 0:
            message = output or "Git завершився з помилкою без тексту."
            if "Could not resolve host" in message or "Failed to connect" in message:
                message = "Немає підключення до GitHub або мережа недоступна."
            raise GitError(message)
        return completed.stdout

