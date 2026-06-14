from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

from .backup_service import BackupService
from .config import UpdaterConfig, get_python_executable
from .git_service import GitService
from .models import (
    BackupResult,
    DependencyInstallError,
    MigrationError,
    UpdateInfo,
)


LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, str], None]


class UpdateService:
    def __init__(self, config: UpdaterConfig) -> None:
        self.config = config
        self.git = GitService(config)
        self.backups = BackupService(config)

    def check_for_updates(self, log: LogCallback | None = None) -> UpdateInfo:
        return self.git.check_for_updates(log=log)

    def install_update(
        self,
        log: LogCallback | None = None,
        progress: ProgressCallback | None = None,
    ) -> BackupResult:
        self._progress(progress, 10, "Створення резервної копії бази")
        backup = self.backups.create_database_backup()
        self._log(log, f"Резервна копія створена: {backup.backup_path}")

        self._progress(progress, 35, "Оновлення коду з GitHub")
        self.git.reset_to_remote(log=log)

        self._progress(progress, 65, "Запуск Django migrations")
        self._run_manage_migrate(log=log)

        self._progress(progress, 85, "Перевірка requirements.txt")
        self._install_requirements_if_needed(log=log)

        self._progress(progress, 100, "Оновлення завершено")
        self._restart_application(log=log)
        return backup

    def _run_manage_migrate(self, log: LogCallback | None = None) -> None:
        manage_py = Path(self.config.manage_py)
        if not manage_py.exists():
            raise MigrationError(f"Файл manage.py не знайдено: {manage_py}")
        command = (get_python_executable(), str(manage_py), "migrate")
        output = self._run_command(command, "Помилка Django migrations", log=log)
        if output:
            self._log(log, output)

    def _install_requirements_if_needed(self, log: LogCallback | None = None) -> None:
        requirements = Path(self.config.requirements_file)
        if not requirements.exists():
            self._log(log, "requirements.txt не знайдено, встановлення залежностей пропущено.")
            return
        command = (get_python_executable(), "-m", "pip", "install", "-r", str(requirements))
        try:
            output = self._run_command(command, "Помилка встановлення залежностей", log=log)
        except MigrationError as exc:
            raise DependencyInstallError(str(exc)) from exc
        if output:
            self._log(log, output)

    def _restart_application(self, log: LogCallback | None = None) -> None:
        if not self.config.restart_command:
            return
        try:
            subprocess.Popen(
                self.config.restart_command,
                cwd=Path(self.config.repo_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._log(log, "Команду перезапуску програми виконано.")
        except OSError as exc:
            self._log(log, f"Оновлення успішне, але перезапуск не виконано: {exc}")

    def _run_command(
        self,
        command: tuple[str, ...],
        error_prefix: str,
        log: LogCallback | None = None,
    ) -> str:
        self._log(log, f"$ {' '.join(command)}")
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
        except OSError as exc:
            raise MigrationError(f"{error_prefix}: {exc}") from exc

        output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
        if completed.returncode != 0:
            raise MigrationError(f"{error_prefix}:\n{output}")
        return output

    @staticmethod
    def _log(log: LogCallback | None, message: str) -> None:
        if log:
            log(message)

    @staticmethod
    def _progress(progress: ProgressCallback | None, value: int, message: str) -> None:
        if progress:
            progress(value, message)

