"""S3: mínimo privilegio en Postgres, con el antes (dueño) y el después (lecreo_app)."""
from __future__ import annotations

import psycopg
import pytest

from app import config, db

pytestmark = pytest.mark.usefixtures("requiere_db")

PROHIBIDAS = [
    "DELETE FROM numeros_reportados",
    "TRUNCATE canales_oficiales",
    "UPDATE dominios_oficiales SET entidad = 'Atacante'",
    "INSERT INTO numeros_reportados (numero, reportes, origen) VALUES ('+573000000099', 99, 'usuario')",
    "DELETE FROM reportes_usuario",
    "UPDATE reportes_usuario SET reportante = 'otro'",
    "DROP TABLE feedback",
    "CREATE TABLE robo (x text)",
    "SELECT senales FROM analisis",
]


def _intentar(url: str, sql: str) -> bool:
    """True si Postgres deja ejecutarla. Siempre se deshace: la prueba no cambia la base."""
    with psycopg.connect(url, connect_timeout=3) as conn:
        try:
            conn.execute(sql)
            return True
        except psycopg.errors.InsufficientPrivilege:
            return False
        finally:
            conn.rollback()


def test_la_app_no_se_conecta_como_el_duenio():
    with db.conexion() as conn:
        usuario = conn.execute("SELECT current_user").fetchone()[0]
    assert usuario == "lecreo_app"
    assert config.DATABASE_URL != config.DATABASE_URL_ADMIN


@pytest.mark.parametrize("sql", PROHIBIDAS)
def test_antes_el_duenio_podia(sql):
    assert _intentar(config.DATABASE_URL_ADMIN, sql) is True


@pytest.mark.parametrize("sql", PROHIBIDAS)
def test_ahora_la_app_no_puede(sql):
    assert _intentar(config.DATABASE_URL, sql) is False


@pytest.mark.parametrize("sql", [
    "SELECT * FROM canales_oficiales LIMIT 1",
    "SELECT * FROM dominios_oficiales LIMIT 1",
    "SELECT * FROM acortadores LIMIT 1",
    "SELECT * FROM numeros_reportados LIMIT 1",
    "SELECT count(*) FROM reportes_usuario",
    "INSERT INTO reportes_usuario (numero, reportante) VALUES ('+573000000098', 'prueba') "
    "ON CONFLICT (numero, reportante) DO UPDATE SET fecha = CURRENT_DATE",
    "INSERT INTO analisis (tipo_entrada, semaforo, ok) VALUES ('texto', 'verde', true) RETURNING id",
])
def test_la_app_si_puede_lo_que_necesita(sql):
    assert _intentar(config.DATABASE_URL, sql) is True
