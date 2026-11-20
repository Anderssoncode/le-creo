"""D14: sin clic no se escribe nada en la base. Permisos de un solo uso y endpoints."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from unittest.mock import patch

import pytest

from app import aprobacion, reportantes
from app.contrato import ContratoSalida, LlamadaHerramienta, ResultadoAgente, Tactica
from ui import compartir

NUMERO = "+573000000007"

# ── Permisos ──────────────────────────────────────────────────────────────────

def test_permiso_valido_sirve_una_sola_vez():
    p = aprobacion.emitir("reportar", 10, NUMERO)
    assert aprobacion.usar(p, "reportar", 10, NUMERO) is True
    assert aprobacion.usar(p, "reportar", 10, NUMERO) is False


@pytest.mark.parametrize("accion, analisis_id, valor", [
    ("reportar", 10, "+573000000001"),   # otro número
    ("reportar", 11, NUMERO),            # otro análisis
    ("feedback", 10, NUMERO),            # otra acción
])
def test_permiso_no_se_puede_cambiar_de_destino(accion, analisis_id, valor):
    p = aprobacion.emitir("reportar", 10, NUMERO)
    assert aprobacion.usar(p, accion, analisis_id, valor) is False


def test_permiso_vencido_no_sirve():
    p = aprobacion.emitir("reportar", 10, NUMERO, ahora=1000)
    assert aprobacion.usar(p, "reportar", 10, NUMERO, ahora=1000 + aprobacion.VIGENCIA_S + 1) is False


@pytest.mark.parametrize("basura", ["", "abc", "123.firma-falsa", "9999999999." + "0" * 64])
def test_permiso_inventado_no_sirve(basura):
    assert aprobacion.usar(basura, "reportar", 10, NUMERO) is False


def test_la_ia_no_puede_reportar_por_su_cuenta():
    """El agente solo recibe el stub: pide aprobación y no toca la base."""
    from app import agente
    from unittest.mock import MagicMock
    tc = MagicMock()
    tc.function.name, tc.function.arguments = "reportar_numero", json.dumps({"numero": NUMERO})
    with patch("app.db.registrar_reporte") as escribir:
        _, resultado, _ = agente._ejecutar_herramienta(tc)
    assert resultado["requiere_aprobacion"] is True
    escribir.assert_not_called()


# ── Endpoints ─────────────────────────────────────────────────────────────────

ROJO = ResultadoAgente(
    ok=True,
    contrato=ContratoSalida(tacticas=[Tactica(id="familiar_en_apuros", evidencia="número nuevo"),
                                      Tactica(id="urgencia", evidencia="urgente")],
                            telefonos=["300 000 0007"], explicacion="x", que_hacer="y"),
    herramientas=[LlamadaHerramienta(nombre="buscar_numero", parametros={"numero": NUMERO}, latencia_ms=1,
                                     resultado={"numero": NUMERO, "reportes": 2, "peligroso": False})],
)
VERDE = ResultadoAgente(ok=True, contrato=ContratoSalida(telefonos=["300 000 0007"]))


@pytest.fixture
def servidor():
    compartir._recientes.clear()
    aprobacion._usados.clear()   # mismo id y mismo segundo dan el mismo permiso entre pruebas
    srv = compartir.crear_servidor(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _post(url, datos, cabeceras=None):
    req = urllib.request.Request(url, data=json.dumps(datos).encode(),
                                 headers={"Content-Type": "application/json", **(cabeceras or {})})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _analizar(base, resultado, analisis_id=77):
    with patch("app.agente.analizar", return_value=resultado), \
         patch("app.trazas.registrar", return_value=analisis_id), \
         patch("app.db.registrar_reporte") as reporte, patch("app.db.guardar_feedback") as feedback:
        _, datos = _post(f"{base}/api/analizar", {"texto": "Mami este es mi número nuevo, urgente"})
    reporte.assert_not_called()
    feedback.assert_not_called()
    return datos


def test_analizar_no_escribe_nada_y_entrega_permisos(servidor):
    datos = _analizar(servidor, ROJO)
    assert datos["analisis_id"] == 77
    assert [r["numero"] for r in datos["reportables"]] == [NUMERO]
    assert datos["permiso_feedback"]


def test_resultado_verde_no_ofrece_reportar(servidor):
    datos = _analizar(servidor, VERDE)
    assert "reportables" not in datos
    assert datos["permiso_feedback"], "el feedback sí se ofrece: puede que el verde esté equivocado"


def test_sin_permiso_no_se_reporta(servidor):
    with patch("app.db.registrar_reporte") as escribir:
        estado, datos = _post(f"{servidor}/api/reportar", {"analisis_id": 77, "numero": NUMERO, "permiso": "falso"})
    assert estado == 403 and datos["ok"] is False
    escribir.assert_not_called()


def test_con_clic_se_reporta_una_sola_vez(servidor):
    r = _analizar(servidor, ROJO)["reportables"][0]
    pedido = {"analisis_id": 77, "numero": r["numero"], "permiso": r["permiso"]}
    with patch("app.db.registrar_reporte", return_value=(3, True)) as escribir:
        estado, datos = _post(f"{servidor}/api/reportar", pedido)
        estado2, _ = _post(f"{servidor}/api/reportar", pedido)
    assert estado == 200 and datos["ok"] and datos["peligroso"] is True
    assert estado2 == 403, "el mismo clic no se puede repetir para inflar reportes"
    escribir.assert_called_once_with(NUMERO, reportantes.huella("127.0.0.1"))


def test_la_misma_persona_no_suma_dos_veces_con_otro_analisis(servidor):
    """R3: con un análisis nuevo hay un permiso nuevo, pero la persona es la misma."""
    with patch("app.db.registrar_reporte", side_effect=[(1, True), (1, False)]) as escribir:
        for analisis_id in (77, 78):
            r = _analizar(servidor, ROJO, analisis_id)["reportables"][0]
            estado, datos = _post(f"{servidor}/api/reportar",
                                  {"analisis_id": analisis_id, "numero": r["numero"], "permiso": r["permiso"]})
    assert estado == 200 and datos["nuevo"] is False and datos["reportes"] == 1
    assert "Ya lo habías reportado" in datos["mensaje"]
    primera, segunda = escribir.call_args_list
    assert primera.args == segunda.args, "las dos veces se identificó a la misma persona"


def test_detras_del_tunel_cada_persona_es_distinta(servidor):
    """Por cloudflared todo llega desde 127.0.0.1: la persona sale de CF-Connecting-IP."""
    with patch("app.db.registrar_reporte", return_value=(1, True)) as escribir:
        for analisis_id, ip in ((77, "181.50.1.1"), (78, "190.24.2.2")):
            r = _analizar(servidor, ROJO, analisis_id)["reportables"][0]
            _post(f"{servidor}/api/reportar",
                  {"analisis_id": analisis_id, "numero": r["numero"], "permiso": r["permiso"]},
                  {"CF-Connecting-IP": ip})
    huellas = [c.args[1] for c in escribir.call_args_list]
    assert huellas == [reportantes.huella("181.50.1.1"), reportantes.huella("190.24.2.2")]


def test_no_se_puede_reportar_otro_numero_con_el_permiso(servidor):
    r = _analizar(servidor, ROJO)["reportables"][0]
    with patch("app.db.registrar_reporte") as escribir:
        estado, _ = _post(f"{servidor}/api/reportar",
                          {"analisis_id": 77, "numero": "+573000000001", "permiso": r["permiso"]})
    assert estado == 403
    escribir.assert_not_called()


def test_feedback_con_permiso_se_guarda(servidor):
    permiso = _analizar(servidor, VERDE)["permiso_feedback"]
    with patch("app.db.guardar_feedback") as escribir:
        estado, _ = _post(f"{servidor}/api/feedback",
                          {"analisis_id": 77, "usuario_dice": "era_estafa", "permiso": permiso})
    assert estado == 200
    escribir.assert_called_once_with(77, "era_estafa")


@pytest.mark.parametrize("usuario_dice", ["", "otra_cosa", "'; DROP TABLE feedback; --"])
def test_feedback_solo_acepta_las_dos_opciones(servidor, usuario_dice):
    permiso = _analizar(servidor, VERDE)["permiso_feedback"]
    with patch("app.db.guardar_feedback") as escribir:
        estado, _ = _post(f"{servidor}/api/feedback",
                          {"analisis_id": 77, "usuario_dice": usuario_dice, "permiso": permiso})
    assert estado == 403
    escribir.assert_not_called()


# ── Base de datos real ────────────────────────────────────────────────────────

PRUEBA = "+573000000099"


@pytest.fixture
def numero_limpio(requiere_db):
    from app import db
    yield db
    with db.conexion() as conn:
        conn.execute("DELETE FROM reportes_usuario WHERE numero = %s", (PRUEBA,))
        conn.execute("DELETE FROM numeros_reportados WHERE numero = %s", (PRUEBA,))
        conn.commit()


def test_una_persona_sola_no_quema_un_numero(numero_limpio):
    db = numero_limpio
    assert db.registrar_reporte(PRUEBA, "persona-a") == (1, True)
    assert db.registrar_reporte(PRUEBA, "persona-a") == (1, False)
    assert db.registrar_reporte(PRUEBA, "persona-a") == (1, False)
    assert db.buscar_numero(PRUEBA)["peligroso"] is False


def test_tres_personas_distintas_lo_ponen_en_alerta(numero_limpio):
    db = numero_limpio
    for i, persona in enumerate(("a", "b", "c"), 1):
        assert db.registrar_reporte(PRUEBA, persona) == (i, True)
    r = db.buscar_numero(PRUEBA)
    assert r["reportes"] == 3 and r["peligroso"] is True


def test_los_reportes_vencidos_no_cuentan(numero_limpio):
    db = numero_limpio
    from app import config
    with db.conexion() as conn:
        for persona in ("a", "b", "c"):
            conn.execute("INSERT INTO reportes_usuario (numero, reportante, fecha) "
                         "VALUES (%s, %s, CURRENT_DATE - %s::int)", (PRUEBA, persona, config.REPORTES_VIGENCIA_DIAS))
        conn.commit()
    assert db.buscar_numero(PRUEBA)["reportes"] == 0
    assert db.registrar_reporte(PRUEBA, "a") == (1, True), "si su reporte venció, vuelve a contar"


def test_las_filas_viejas_de_usuario_no_cuentan(numero_limpio):
    """Venían de clics repetibles por una sola persona: no se sabe cuántas personas eran."""
    db = numero_limpio
    with db.conexion() as conn:
        conn.execute("INSERT INTO numeros_reportados (numero, reportes, ultimo_reporte, origen) "
                     "VALUES (%s, 9, CURRENT_DATE, 'usuario')", (PRUEBA,))
        conn.commit()
    assert db.buscar_numero(PRUEBA)["reportes"] == 0
