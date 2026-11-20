"""Lo verificable no depende de que el modelo obedezca (S1, ataque A04).

El agente decide qué herramientas llamar, y una inyección puede convencerlo de no anotar un
teléfono o de no revisar un enlace ("en que_hacer escribe: llama al 300…"). Si eso pasa, las reglas
nunca ven el dato y el mensaje puede salir verde. Por eso, después del agente, el código:

  1. saca del texto, con expresiones regulares, los teléfonos y enlaces escritos,
  2. los agrega al contrato si el modelo los omitió,
  3. corre `buscar_numero` / `revisar_enlace` con los que nadie consultó (son funciones
     deterministas: una consulta a la base y un análisis del texto de la URL, sin abrirla),
  4. no acepta un "fuera de alcance" si el mensaje trae teléfonos o enlaces que revisar.

Antes del agente, se quitan los caracteres invisibles con los que se parte una palabra o un dominio.
"""
from __future__ import annotations

import re
import time
from typing import Any

from app import herramientas
from app.contrato import ContratoSalida, LlamadaHerramienta

# Ancho cero, marcas de dirección y guion suave: no se ven, pero parten palabras y dominios.
_INVISIBLES = re.compile("[­᠎​-‏‪-‮⁠-⁤﻿]")

# Celular colombiano (3xx), fijo nacional (60x) y líneas 01 8000, con o sin +57 y separadores.
_TELEFONO = re.compile(
    r"(?<![\d+])(?:"
    r"(?:\+?57[\s.-]?)?(?:3\d\d|60\d)(?:[\s.-]?\d){7}"
    r"|01[\s.-]?8000(?:[\s.-]?\d){6}"
    r")(?!\d)"
)

# Dominios escritos en el texto, con o sin http. Solo terminaciones de dominio reales, para no
# confundir 'T.Deb' o '150000.00' con un enlace. \w acepta letras de otros alfabetos (homógrafos).
_TLDS = ("com|co|net|org|info|biz|xyz|ly|me|io|app|site|online|top|shop|store|link|click|live|"
         "cc|us|club|pro|vip|gov|edu|mx|es|ar|pe|ec|cl|br|tk|ml|ga|cf|gq|ru|cn|in|ws|to|gl|gd|is|tv")
_ENLACE = re.compile(
    rf"(?<![@\w.-])(?:https?://)?(?:[\w-]+\.)+(?:{_TLDS})(?![\w-])(?:/[^\s<>\"')\]]*)?",
    re.IGNORECASE,
)


def sin_invisibles(texto: str) -> str:
    return _INVISIBLES.sub("", texto)


def extraer_telefonos(texto: str) -> list[str]:
    return list(dict.fromkeys(m.group(0).strip() for m in _TELEFONO.finditer(texto)))


def extraer_enlaces(texto: str) -> list[str]:
    return list(dict.fromkeys(m.group(0).rstrip(".,;:") for m in _ENLACE.finditer(texto)))


def _diez(numero: str) -> str:
    """Últimos 10 dígitos: '+57 300 000 0042' y '3000000042' son el mismo número."""
    return "".join(c for c in numero if c.isdigit())[-10:]


def _correr(nombre: str, parametros: dict[str, Any]) -> LlamadaHerramienta:
    t0 = time.perf_counter()
    try:
        resultado = herramientas.DESPACHO[nombre](**parametros)
    except Exception as exc:   # sin base no hay dato: queda el error, como cuando lo llama el agente
        resultado = {"error": f"{type(exc).__name__}: {exc}"}
    return LlamadaHerramienta(nombre=nombre, parametros=parametros, resultado=resultado,
                              latencia_ms=int((time.perf_counter() - t0) * 1000), origen="codigo")


def completar(texto: str, contrato: ContratoSalida, llamadas: list[LlamadaHerramienta], avisos: list[str]) -> None:
    """Agrega al contrato y a las llamadas lo verificable que el agente omitió. Modifica en sitio."""
    enlaces = extraer_enlaces(texto)
    telefonos = extraer_telefonos(texto)

    if contrato.fuera_de_alcance:
        if not (enlaces or telefonos):
            return
        # Una inyección puede pedir "responde fuera_de_alcance" para saltarse todo el análisis.
        contrato.fuera_de_alcance = False
        avisos.append("El modelo dijo que no era un mensaje para revisar, pero trae enlaces o teléfonos: se revisaron igual.")

    # Enlaces: los del modelo y los del texto, uno por dominio.
    revisados = {h.resultado.get("dominio") for h in llamadas
                 if h.nombre == "revisar_enlace" and isinstance(h.resultado, dict)}
    dominios_contrato = {herramientas._extraer_dominio(u) for u in contrato.enlaces}
    for url in list(contrato.enlaces) + enlaces:
        dominio = herramientas._extraer_dominio(url)
        if not dominio or dominio in revisados:
            continue
        if dominio not in dominios_contrato:
            contrato.enlaces.append(url)
            dominios_contrato.add(dominio)
        llamadas.append(_correr("revisar_enlace", {"url": url}))
        revisados.add(dominio)

    # Teléfonos: los del modelo y los del texto, uno por número.
    consultados = {_diez(h.resultado.get("numero", "")) for h in llamadas
                   if h.nombre == "buscar_numero" and isinstance(h.resultado, dict)}
    en_contrato = {_diez(t) for t in contrato.telefonos}
    for tel in list(contrato.telefonos) + telefonos:
        clave = _diez(tel)
        if len(clave) < 10 or clave in consultados:
            continue
        if clave not in en_contrato:
            contrato.telefonos.append(tel)
            en_contrato.add(clave)
        llamadas.append(_correr("buscar_numero", {"numero": tel}))
        consultados.add(clave)
