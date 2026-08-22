"""过期上传与结果文件的定期清理。"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from utils.config import load_settings, project_path

logger = logging.getLogger(__name__)

DEFAULT_MAX_AGE_DAYS = 7
_CLEANUP_DIRS = ("uploads_dir", "results_dir")


def prune_stale_files(max_age_days: int | None = None) -> int:
    settings = load_settings()
    days = max_age_days if max_age_days is not None else int(
        settings.get("cleanup", {}).get("max_age_days", DEFAULT_MAX_AGE_DAYS)
    )
    if days <= 0:
        return 0

    cutoff = time.time() - days * 86400
    removed = 0
    for key in _CLEANUP_DIRS:
        directory = project_path(settings["paths"][key])
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            try:
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                logger.warning("Failed to remove stale file %s.", path, exc_info=True)

    if removed:
        logger.info("Pruned %d files older than %d days.", removed, days)
    return removed
