"""db 层回归测试（P2-12：连接必须显式关闭，事务语义正确）。"""

import sqlite3

import pytest

from app import db


def test_connection_context_closes_and_commits():
    conn = None
    with db.connection() as conn:
        assert not _is_closed(conn)
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('t', '1')")

    # with 块结束后连接必须已关闭
    assert _is_closed(conn)
    # 写入已提交，新连接能读到
    with db.connection() as check:
        row = check.execute("SELECT value FROM meta WHERE key='t'").fetchone()
        assert row["value"] == "1"


def _is_closed(conn) -> bool:
    """sqlite3.Connection 没有 is_closed 属性；关闭后 execute 会抛 ProgrammingError。"""
    try:
        conn.execute("SELECT 1")
        return False
    except sqlite3.ProgrammingError:
        return True


def test_connection_context_rolls_back_on_error():
    with pytest.raises(RuntimeError, match="boom"):
        with db.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('t2', '1')")
            raise RuntimeError("boom")

    with db.connection() as check:
        assert check.execute("SELECT value FROM meta WHERE key='t2'").fetchone() is None


def test_plain_connect_still_works_for_explicit_control():
    """低层 db.connect() 保留（health 探活等场景），但业务端点一律用 db.connection()。"""
    conn = db.connect()
    try:
        conn.execute("PRAGMA busy_timeout")
    finally:
        conn.close()
    assert _is_closed(conn)