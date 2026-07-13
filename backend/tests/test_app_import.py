import importlib
import sys


def test_app_imports_without_db_connection(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/hcp_crm")
    sys.modules.pop("app.main", None)
    sys.modules.pop("app.database", None)
    sys.modules.pop("app.models", None)
    sys.modules.pop("app.schemas", None)
    sys.modules.pop("app.agent", None)
    sys.modules.pop("app.config", None)

    module = importlib.import_module("app.main")

    assert hasattr(module, "app")
    assert module.app.title.startswith("AI-First CRM")
