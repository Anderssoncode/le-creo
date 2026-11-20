"""Quién reporta un número, sin guardar quién es (R3 del plan, regla 3).

Un número queda en alerta con reportes de 3 personas distintas, no con 3 clics. Para saber si
dos reportes vienen de la misma persona se usa su IP, pero en la base solo queda una huella
HMAC: sin la clave no se puede volver a la IP, ni siquiera probando todas las IPv4 posibles.

La clave sale de LECREO_SECRETO o, si no está, de un archivo .secreto que se crea una vez en la
raíz del proyecto (está en .gitignore). Tiene que ser estable: si cambiara en cada arranque,
la misma persona contaría como nueva después de reiniciar la app.

Límite conocido: personas detrás de la misma IP (misma red wifi, o un operador móvil con NAT)
cuentan como una sola. Falla hacia el lado seguro: es más difícil quemar un número, no más fácil.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import secrets
from pathlib import Path

RUTA_SECRETO = Path(__file__).parent.parent / ".secreto"
_clave: bytes | None = None


def _cargar_clave() -> bytes:
    global _clave
    if _clave is None:
        if desde_env := os.getenv("LECREO_SECRETO", "").strip():
            _clave = desde_env.encode()
        elif RUTA_SECRETO.exists():
            _clave = RUTA_SECRETO.read_text(encoding="utf-8").strip().encode()
        else:
            nueva = secrets.token_hex(32)
            RUTA_SECRETO.write_text(nueva, encoding="utf-8")
            _clave = nueva.encode()
    return _clave


def _red(ip: str) -> str:
    """Un celular con IPv6 cambia de dirección dentro de su /64: se cuenta la red, no la dirección."""
    try:
        direccion = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if direccion.version == 6:
        if direccion.ipv4_mapped:
            return str(direccion.ipv4_mapped)
        return str(ipaddress.ip_network(f"{direccion}/64", strict=False))
    return str(direccion)


def huella(ip: str) -> str:
    """Identificador del reportante: igual para la misma persona, irreversible sin la clave."""
    return hmac.new(_cargar_clave(), _red(ip).encode(), hashlib.sha256).hexdigest()[:32]
