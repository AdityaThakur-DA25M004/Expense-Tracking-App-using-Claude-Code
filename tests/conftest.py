import sqlite3
import pytest
import database.db as db_module
from app import app as flask_app
from database.db import init_db


@pytest.fixture
def app(tmp_path):
    db_file = str(tmp_path / "test.db")
    original_get_db = db_module.get_db

    def _test_get_db():
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    db_module.get_db = _test_get_db
    init_db()

    flask_app.config["TESTING"] = True
    yield flask_app

    db_module.get_db = original_get_db


@pytest.fixture
def client(app):
    return app.test_client()
