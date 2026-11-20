"""R3: la huella de quien reporta identifica a la persona sin guardar su IP."""
from __future__ import annotations

from app import reportantes


def test_misma_ip_misma_huella():
    assert reportantes.huella("181.50.1.1") == reportantes.huella("181.50.1.1")


def test_ips_distintas_huellas_distintas():
    assert reportantes.huella("181.50.1.1") != reportantes.huella("181.50.1.2")


def test_la_huella_no_contiene_la_ip():
    h = reportantes.huella("181.50.1.1")
    assert "181" not in h and len(h) == 32


def test_ipv6_cuenta_la_red_no_la_direccion():
    """Un celular con IPv6 cambia de dirección dentro de su /64 sin cambiar de persona."""
    assert reportantes.huella("2800:e2:1:2::a") == reportantes.huella("2800:e2:1:2::ffff")
    assert reportantes.huella("2800:e2:1:2::a") != reportantes.huella("2800:e2:1:3::a")


def test_ipv4_dentro_de_ipv6_es_la_misma_persona():
    assert reportantes.huella("::ffff:181.50.1.1") == reportantes.huella("181.50.1.1")


def test_sin_la_clave_no_se_puede_reconstruir(monkeypatch):
    antes = reportantes.huella("181.50.1.1")
    monkeypatch.setattr(reportantes, "_clave", b"otra-clave")
    assert reportantes.huella("181.50.1.1") != antes


def test_sin_env_la_clave_se_crea_una_vez_y_se_reutiliza(monkeypatch, tmp_path):
    ruta = tmp_path / ".secreto"
    monkeypatch.delenv("LECREO_SECRETO", raising=False)
    monkeypatch.setattr(reportantes, "RUTA_SECRETO", ruta)
    monkeypatch.setattr(reportantes, "_clave", None)
    primera = reportantes.huella("181.50.1.1")
    assert ruta.exists()
    monkeypatch.setattr(reportantes, "_clave", None)   # como si la app se reiniciara
    assert reportantes.huella("181.50.1.1") == primera
