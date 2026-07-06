from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "settings.yaml"


@lru_cache(maxsize=1)
def load_settings(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    with path.open("r", encoding="utf-8") as file:
        settings = yaml.safe_load(file) or {}
    return settings


def project_path(relative_path: str | Path) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def ensure_project_dirs() -> None:
    settings = load_settings()
    for key in ("samples_dir", "uploads_dir", "results_dir"):
        project_path(settings["paths"][key]).mkdir(parents=True, exist_ok=True)
    project_path("data/models").mkdir(parents=True, exist_ok=True)
    project_path("data/datasets/wall_defects").mkdir(parents=True, exist_ok=True)
