"""Muestra una traza en la consola, legible, para la sustentación ("muéstrenme la traza").

Uso:
  python scripts/ver_traza.py 669       un análisis de este computador (trazas/AAAA-MM-DD.jsonl)
  python scripts/ver_traza.py ultima    el último análisis (por ejemplo, el que acaba de hacer el voluntario)
  python scripts/ver_traza.py A04       un ataque de S1, antes y después (docs/evidencia/s1_ataques_*.json)

La traza nunca tiene el texto del mensaje (regla 3): solo qué consultó el agente, qué devolvió
cada herramienta y qué señales tomó reglas.py para decidir el color.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TRAZAS = RAIZ / "trazas"
EVIDENCIA = RAIZ / "docs" / "evidencia"
COLOR = {"rojo": "🔴 ROJO", "amarillo": "🟡 AMARILLO", "verde": "🟢 VERDE", "rechazo": "⚪ RECHAZO", "error": "⚠️ ERROR"}


def _linea(texto: str = "", ancho: int = 72) -> None:
    print(texto if texto else "─" * ancho)


def _resultado(valor) -> str:
    if isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except json.JSONDecodeError:
            return valor[:160]
    if isinstance(valor, dict):
        claves = ("numero", "reportes", "peligroso", "encontrada", "entidad", "dominio", "es_oficial", "imita_a", "es_acortador")
        partes = [f"{k}={valor[k]}" for k in claves if k in valor]
        return ", ".join(partes) or json.dumps(valor, ensure_ascii=False)[:160]
    return str(valor)[:160]


def mostrar_local(clave: str) -> int:
    registros = []
    for archivo in sorted(TRAZAS.glob("*.jsonl")):
        registros += [json.loads(l) for l in archivo.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not registros:
        print("No hay trazas en este computador todavía (carpeta trazas/).")
        return 1
    d = registros[-1] if clave == "ultima" else next((r for r in registros if str(r.get("analisis_id")) == clave), None)
    if d is None:
        print(f"No encontré el análisis #{clave} en trazas/. Últimos: {[r.get('analisis_id') for r in registros[-5:]]}")
        return 1
    _linea()
    print(f"  Análisis #{d.get('analisis_id')}  ·  {d.get('fecha', '')[:19].replace('T', ' ')} UTC  ·  entrada: {d.get('tipo_entrada', 'texto')}")
    print(f"  Resultado: {COLOR.get(d.get('semaforo'), d.get('semaforo'))}")
    print(f"  {d.get('proveedor')} / {d.get('modelo')}  ·  {d.get('latencia_ms')} ms  ·  "
          f"{d.get('tokens_in', 0) + d.get('tokens_out', 0)} tokens  ·  {d.get('iteraciones')} pasos del agente")
    _linea()
    print("  QUÉ CONSULTÓ (en orden)")
    for h in d.get("herramientas", []):
        quien = "el código" if h.get("origen") == "codigo" else "el agente"
        print(f"   {h.get('orden')}. {h.get('nombre')}({json.dumps(h.get('parametros'), ensure_ascii=False)})  ← lo pidió {quien}")
        print(f"      → {_resultado(h.get('resultado_resumido'))}   ({h.get('latencia_ms')} ms)")
    if not d.get("herramientas"):
        print("   (ninguna)")
    print()
    print("  SEÑALES QUE TOMÓ reglas.py PARA DECIDIR EL COLOR")
    for s in d.get("senales", []) or ["(ninguna)"]:
        print(f"   · {s}")
    for a in d.get("avisos", []) or []:
        print(f"   ⚠ aviso: {a}")
    _linea()
    print("  El texto del mensaje no se guarda (regla 3).")
    return 0


def mostrar_ataque(ataque: str) -> int:
    archivos = sorted(EVIDENCIA.glob("s1_ataques_*.json"))
    encontrados = 0
    for archivo in archivos:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
        for a in datos.get("ataques", []):
            if a.get("id", "").upper() != ataque.upper():
                continue
            encontrados += 1
            etapa = archivo.stem.replace("s1_ataques_", "")
            _linea()
            print(f"  {a['id']} · {etapa} · traza #{a.get('analisis_id')} · {COLOR.get(a.get('semaforo'), a.get('semaforo'))}")
            print(f"  Técnica: {a.get('tecnica')}")
            print(f"  ¿Logró su objetivo?: {'SÍ' if a.get('logro_su_objetivo') else 'no'} · {a.get('detalle', '')}")
            print("  Consultó:")
            for h in a.get("herramientas", []):
                origen = " (lo completó el código)" if h.get("origen") == "codigo" else ""
                print(f"   · {h.get('nombre')}({json.dumps(h.get('parametros'), ensure_ascii=False)}) → {_resultado(h.get('resultado'))}{origen}")
            print("  Lo que vio la persona:")
            for l in (a.get("lo_que_ve_la_persona") or [])[:3]:
                print(f"   │ {l}")
    if not encontrados:
        print(f"No encontré {ataque} en {EVIDENCIA}.")
        return 1
    _linea()
    print("  Detalle y arreglos: docs/seguridad.md §3")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    clave = sys.argv[1]
    sys.exit(mostrar_ataque(clave) if clave.upper().startswith("A") and clave[1:].isdigit() else mostrar_local(clave))
