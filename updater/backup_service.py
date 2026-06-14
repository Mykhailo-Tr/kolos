from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .config import UpdaterConfig
from .models import BackupError, BackupResult


class BackupService:
    def __init__(self, config: UpdaterConfig) -> None:
        self.config = config

    def create_database_backup(self) -> BackupResult:
        source_path = Path(self.config.database_path)
        if not source_path.exists():
            raise BackupError(f"Базу даних не знайдено: {source_path}")
        if not source_path.is_file():
            raise BackupError(f"Шлях до бази даних не є файлом: {source_path}")

        created_at = datetime.now()
        target_dir = Path(self.config.backups_dir)
        if self.config.use_daily_backup_folders:
            target_dir = target_dir / created_at.strftime("%Y-%m-%d")

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            backup_path = target_dir / f"db_backup_{created_at:%Y-%m-%d_%H-%M-%S}.sqlite3"
            # copy2 preserves timestamps and metadata where Windows permits it.
            shutil.copy2(source_path, backup_path)
        except OSError as exc:
            raise BackupError(f"Не вдалося створити резервну копію: {exc}") from exc

        return BackupResult(source_path=source_path, backup_path=backup_path, created_at=created_at)

