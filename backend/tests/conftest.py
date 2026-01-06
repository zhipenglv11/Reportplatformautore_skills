import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    storage_path = tmp_path / "storage"
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_BASE_PATH", str(storage_path))

    import config as config_module

    importlib.reload(config_module)

    import models.db as db_module

    importlib.reload(db_module)

    schema_path = Path(__file__).resolve().parents[1] / "database" / "init_sqlite.sql"
    schema = schema_path.read_text(encoding="utf-8")
    engine = db_module.get_engine()
    with engine.begin() as conn:
        for statement in schema.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.exec_driver_sql(stmt)

    import main as main_module

    importlib.reload(main_module)
    return main_module.app


@pytest.fixture
def client(app):
    return TestClient(app)
