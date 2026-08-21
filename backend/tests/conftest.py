import pytest

from app import db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """每个测试使用独立的临时数据库，绝不触碰真实数据目录。"""
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test-app.db")
    monkeypatch.setattr(db, "BACKUP_DIR", tmp_path / "backups")
    db.init_db()
    yield