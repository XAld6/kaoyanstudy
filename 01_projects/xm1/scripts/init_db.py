from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import init_db
from utils.config import ensure_project_dirs


def main() -> None:
    ensure_project_dirs()
    init_db()
    print("SQLite database initialized: data/inspection.db")


if __name__ == "__main__":
    main()
