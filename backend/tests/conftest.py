"""
Test fixtures for backend tests.

Uses a temporary SQLite database for each test session to avoid
polluting the real data/app.db.
"""

import pytest
import backend.database as db_mod


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    """每个测试用例使用独立的临时数据库"""
    db_path = str(tmp_path / "test.db")
    db_mod._DB_PATH = db_path
    db_mod._connection = None
    db_mod.init_db()
    yield
    conn = db_mod._connection
    if conn:
        conn.close()
        db_mod._connection = None
