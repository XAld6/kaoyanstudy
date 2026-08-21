"""SQLite 持久化层：表结构、连接、初始化与备份。

只用标准库 sqlite3，不加 ORM。数据文件路径由环境变量 KAOYAN_DB_PATH 指定
（VPS 上位于 /opt/kaoyan-console/data/app.db，在 git 检出目录之外）。
"""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(
    os.getenv("KAOYAN_DB_PATH", str(Path(__file__).resolve().parent.parent / "data" / "app.db"))
)
BACKUP_DIR = Path(
    os.getenv("KAOYAN_BACKUP_DIR", str(DB_PATH.parent.parent / "backups"))
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS subjects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  color TEXT NOT NULL,
  weekly_target_hours REAL NOT NULL,
  sort_order INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  title TEXT NOT NULL,
  date TEXT NOT NULL,
  estimated_minutes INTEGER NOT NULL,
  actual_minutes INTEGER NOT NULL,
  priority TEXT NOT NULL,
  status TEXT NOT NULL,
  sort_order INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_date ON tasks(date);
CREATE TABLE IF NOT EXISTS reviews (
  date TEXT PRIMARY KEY,
  text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS focus_stats (
  date TEXT PRIMARY KEY,
  focus_minutes INTEGER NOT NULL,
  pomodoro_count INTEGER NOT NULL,
  session_count INTEGER NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    """每请求新建连接；连接本身廉价，且天然线程安全。

    不设 check_same_thread=False —— 每个请求在自己的线程里使用独立连接。
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db() -> None:
    """建目录、建表、开 WAL。幂等，可安全重复调用。"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO meta (key, value) VALUES ('revision', '0')")
        conn.commit()
    finally:
        conn.close()


def backup_db_to(dest: Path) -> None:
    """用 sqlite3 备份 API 复制一致快照（WAL 模式下 cp 会拿到不一致副本）。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(DB_PATH)
    try:
        dst = sqlite3.connect(dest)
        try:
            with dst:
                src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()