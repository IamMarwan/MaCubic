import os
import pytest
@pytest.fixture(autouse=True)
def isolated_db(tmp_path,monkeypatch):
    monkeypatch.setenv("APP_DB_PATH",str(tmp_path/"test.db"))
    # app.storage reads config at import; update its module-level path as well.
    from app import storage
    storage.DB_PATH=str(tmp_path/"test.db")
