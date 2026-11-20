"""Conexión a Postgres. Las herramientas del agente solo hacen SELECT.

Las únicas escrituras (al final) son las que la persona aprueba con un clic (D14); el agente
no tiene forma de llamarlas.
"""
from __future__ import annotations

import unicodedata
from contextlib import contextmanager
from typing import Any

import psycopg

from app import config
from app.config import DATABASE_URL


@contextmanager
def conexion():
    """Conexión de la app: usuario lecreo_app, con permisos mínimos (db/02_permisos.sql)."""
    # Si Postgres no responde, falla en segundos en vez de consumir el timeout del análisis.
    with psycopg.connect(DATABASE_URL, connect_timeout=3) as conn:
        yield conn


@contextmanager
def conexion_admin():
    """Dueño de la base. Solo para administrar (semillas, limpieza de pruebas), nunca desde la app."""
    with psycopg.connect(config.DATABASE_URL_ADMIN, connect_timeout=3) as conn:
        yield conn


UMBRAL_PELIGROSO = 3


def _contar_reportes(conn: psycopg.Connection, numero: str) -> tuple[int, Any]:
    """(reportes, último) = semilla ficticia + personas distintas con un reporte vigente (R3).

    Las filas antiguas de numeros_reportados con origen 'usuario' no se cuentan: venían de
    clics que una sola persona podía repetir y no hay forma de saber cuántas personas eran."""
    fila = conn.execute(
        """SELECT
             COALESCE((SELECT reportes FROM numeros_reportados
                       WHERE numero = %(n)s AND origen = 'semilla_ficticia'), 0) + count(*),
             GREATEST((SELECT ultimo_reporte FROM numeros_reportados
                       WHERE numero = %(n)s AND origen = 'semilla_ficticia'), max(fecha))
           FROM reportes_usuario
           WHERE numero = %(n)s AND fecha > CURRENT_DATE - %(dias)s::int""",
        {"n": numero, "dias": config.REPORTES_VIGENCIA_DIAS},
    ).fetchone()
    return int(fila[0]), fila[1]


def buscar_numero(numero: str) -> dict[str, Any]:
    """Devuelve reportes del número. Si no tiene, reportes=0."""
    with conexion() as conn:
        reportes, ultimo = _contar_reportes(conn, numero)

    if reportes == 0:
        return {
            "numero": numero,
            "reportes": 0,
            "peligroso": False,
            "ultimo_reporte": None,
            "nota": "Sin reportes no significa seguro.",
        }
    return {
        "numero": numero,
        "reportes": reportes,
        "peligroso": reportes >= UMBRAL_PELIGROSO,
        "ultimo_reporte": str(ultimo) if ultimo else None,
    }


def dominios_oficiales() -> list[tuple[str, str]]:
    """Devuelve todos los dominios oficiales como lista de (dominio, entidad)."""
    with conexion() as conn:
        filas = conn.execute("SELECT dominio, entidad FROM dominios_oficiales").fetchall()
    return [(f[0], f[1]) for f in filas]


def es_acortador(dominio: str) -> bool:
    """True si el dominio está en la tabla de acortadores."""
    with conexion() as conn:
        fila = conn.execute(
            "SELECT 1 FROM acortadores WHERE dominio = %s", (dominio,)
        ).fetchone()
    return fila is not None


def _clave_entidad(texto: str) -> str:
    """'Inter Rapidísimo' → 'interrapidisimo'; ignora tildes, mayúsculas y signos."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "".join(c for c in sin_tildes.lower() if c.isalnum())


def canal_oficial(entidad: str) -> dict[str, Any]:
    """Devuelve canales oficiales de la entidad.

    Coincidencia exacta normalizada; si no hay, la entidad de la tabla más larga
    contenida en el nombre recibido (ej. 'Bancolombia S.A.' → Bancolombia).
    """
    with conexion() as conn:
        filas = conn.execute(
            """SELECT entidad, sector, canales, nunca_pide, fuente_url, verificado_en
               FROM canales_oficiales"""
        ).fetchall()

    buscada = _clave_entidad(entidad)
    fila = next((f for f in filas if _clave_entidad(f[0]) == buscada), None)
    if fila is None and buscada:
        contenidas = [f for f in filas if _clave_entidad(f[0]) and _clave_entidad(f[0]) in buscada]
        fila = max(contenidas, key=lambda f: len(_clave_entidad(f[0])), default=None)

    if fila is None:
        return {"encontrada": False, "entidad": entidad}
    return {
        "encontrada": True,
        "entidad":       fila[0],
        "sector":        fila[1],
        "canales":       fila[2],
        "nunca_pide":    fila[3],
        "fuente_url":    fila[4],
        "verificado_en": str(fila[5]),
    }


# ── Escrituras aprobadas por la persona (D14) ─────────────────────────────────

def registrar_reporte(numero: str, reportante: str) -> tuple[int, bool]:
    """Registra el reporte aprobado de una persona. Devuelve (total, cuenta_como_nuevo).

    Si esa persona ya tenía un reporte vigente del número, no suma: solo renueva la fecha."""
    with conexion() as conn:
        ya_estaba = conn.execute(
            """SELECT 1 FROM reportes_usuario
               WHERE numero = %s AND reportante = %s AND fecha > CURRENT_DATE - %s::int""",
            (numero, reportante, config.REPORTES_VIGENCIA_DIAS),
        ).fetchone()
        conn.execute(
            """INSERT INTO reportes_usuario (numero, reportante) VALUES (%s, %s)
               ON CONFLICT (numero, reportante) DO UPDATE SET fecha = CURRENT_DATE""",
            (numero, reportante),
        )
        conn.commit()
        total, _ = _contar_reportes(conn, numero)
    return total, ya_estaba is None


def guardar_feedback(analisis_id: int, usuario_dice: str) -> None:
    """'era_estafa' | 'no_era_estafa' para un análisis ya registrado."""
    with conexion() as conn:
        conn.execute(
            "INSERT INTO feedback (analisis_id, usuario_dice) VALUES (%s, %s)",
            (analisis_id, usuario_dice),
        )
        conn.commit()
