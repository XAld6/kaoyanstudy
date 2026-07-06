import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENCLAW_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("OPENCLAW_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("OPENCLAW_OUTPUT_DIR", str(tmp_path / "outputs"))
    monkeypatch.setenv("OPENCLAW_DB_PATH", str(tmp_path / "records.db"))

    import app.storage as storage
    import app.main as main

    importlib.reload(storage)
    importlib.reload(main)

    with TestClient(main.app) as test_client:
        yield test_client
