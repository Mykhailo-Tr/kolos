from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT_DIR / "updater_config.json"


@dataclass(frozen=True)
class UpdaterConfig:
    repo_dir: Path = ROOT_DIR
    remote_name: str = "origin"
    branch_name: str = "main"
    manage_py: Path = ROOT_DIR / "manage.py"
    database_path: Path = ROOT_DIR / "db.sqlite3"
    backups_dir: Path = ROOT_DIR / "backups"
    use_daily_backup_folders: bool = True
    requirements_file: Path = ROOT_DIR / "requirements.txt"
    auto_check_on_start: bool = True
    restart_command: tuple[str, ...] = ()

    @property
    def remote_branch(self) -> str:
        return f"{self.remote_name}/{self.branch_name}"


def _default_python() -> str:
    venv_python = ROOT_DIR / "venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _coerce_path(value: Any) -> Path:
    path = Path(str(value))
    if not path.is_absolute():
        return ROOT_DIR / path
    return path


def _coerce_restart_command(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(part) for part in value if str(part).strip())
    if isinstance(value, str) and value.strip():
        return tuple(value.strip().split())
    return ()


def load_config() -> UpdaterConfig:
    config_data: dict[str, Any] = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)

    env_restart = os.getenv("KOLOS_RESTART_COMMAND")
    if env_restart:
        config_data["restart_command"] = env_restart

    values: dict[str, Any] = {}
    path_fields = {"repo_dir", "manage_py", "database_path", "backups_dir", "requirements_file"}

    for field in fields(UpdaterConfig):
        if field.name not in config_data:
            continue
        value = config_data[field.name]
        if field.name in path_fields:
            values[field.name] = _coerce_path(value)
        elif field.name == "restart_command":
            values[field.name] = _coerce_restart_command(value)
        else:
            values[field.name] = value

    return UpdaterConfig(**values)


def save_config(config: UpdaterConfig) -> None:
    data = asdict(config)
    for key, value in data.items():
        if isinstance(value, Path):
            try:
                data[key] = str(value.relative_to(ROOT_DIR))
            except ValueError:
                data[key] = str(value)
        elif isinstance(value, tuple):
            data[key] = list(value)

    with CONFIG_PATH.open("w", encoding="utf-8") as config_file:
        json.dump(data, config_file, ensure_ascii=False, indent=2)


def get_python_executable() -> str:
    return _default_python()

