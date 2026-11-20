from __future__ import annotations

import psycopg
import pytest

from app.config import DATABASE_URL

_estado_db: dict[str, str | None] = {}


@pytest.fixture(autouse=True)
def _clave_de_prueba(monkeypatch):
    """Las pruebas no deben crear el archivo .secreto real del proyecto."""
    from app import reportantes
    monkeypatch.setattr(reportantes, "_clave", b"clave-de-prueba")


@pytest.fixture
def requiere_db():
    """Salta el test al instante si Postgres no está arriba, en vez de colgarse reintentando."""
    if "error" not in _estado_db:
        try:
            psycopg.connect(DATABASE_URL, connect_timeout=3).close()
            _estado_db["error"] = None
        except psycopg.OperationalError as exc:
            _estado_db["error"] = type(exc).__name__
    if _estado_db["error"]:
        pytest.skip("Postgres no está arriba: abre Docker Desktop y corre `docker compose up -d`")
