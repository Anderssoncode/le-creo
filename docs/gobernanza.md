# Ficha de gobernanza de ¿Le creo?

> Momento 3 · entregable obligatorio. Describe lo que el sistema **hace hoy** (2026-11-20), no lo que nos gustaría que hiciera. Cada respuesta enlaza la línea de código o la prueba que la demuestra. Lo que todavía no hace está dicho como tal, en la sección de cada pregunta.
>
> **Nota del equipo:** las cinco preguntas de la semana 13 no están publicadas en la página del curso. Esta ficha responde las cinco que piden la rúbrica y la sustentación: quién decide, dónde se exige la supervisión humana, qué datos se tocan, qué hacemos si causa un daño y cómo se audita. *Revisar la redacción contra la lista que dio el profesor en clase.*

**Qué es:** una segunda opinión sobre un mensaje sospechoso de WhatsApp o SMS, **antes de pagar**. Es para personas mayores y su familia. Responde con un semáforo, el truco que usan y qué hacer.

**Qué no es:** no bloquea transferencias, no es asesoría financiera ni legal, y no garantiza que un mensaje sea seguro. Un 🟢 siempre dice *"No encontramos señales, pero si dudas, llama tú a la línea oficial"* ([`app/respuesta.py:19`](../app/respuesta.py#L19)). Las preguntas que no son sobre un mensaje se rechazan (caso c10 de la suite).

---

## 1. ¿Qué decide la IA y qué decide el sistema?

| Decisión | ¿Quién la toma? | Dónde |
|---|---|---|
| Entender el mensaje: qué entidad dice ser, qué pide, qué truco usa, en palabras simples | **La IA** (Gemini) | [`app/agente.py`](../app/agente.py), contrato validado con pydantic en [`app/contrato.py`](../app/contrato.py) |
| Qué herramientas consultar | **La IA**, con un tope: 5 pasos, 20 s y 8.000 tokens | [`app/agente.py:113`](../app/agente.py#L113), valores en `.env` |
| Revisar todos los teléfonos y enlaces escritos, aunque la IA los salte | **El código** | [`app/verificacion.py`](../app/verificacion.py) |
| **El color del semáforo** | **El código**, con reglas fijas sobre datos verificados. La IA no puede elegirlo | [`app/reglas.py:36`](../app/reglas.py#L36) |
| La primera línea en grande ("NO pagues ni abras enlaces") | **El código**, según el color | [`app/respuesta.py:29`](../app/respuesta.py#L29) |
| El número del botón "Llamar" | **El código**, solo de la tabla verificada. Un número escrito por la IA nunca llega a ser botón | [`app/respuesta.py:129`](../app/respuesta.py#L129), prueba `test_el_boton_nunca_sale_del_modelo` |
| Si un mensaje con un teléfono dudoso sale 🟡, el paso a seguir | **El código** ("No llames ni respondas a los números del mensaje…") | [`app/respuesta.py:83`](../app/respuesta.py#L83) |
| Reportar un número o dar una opinión | **La persona**, con su clic | Pregunta 2 |

**Por qué está repartido así:** la IA hace lo que no se puede programar con reglas, que es entender español informal, errores y emojis, y explicar el truco. Lo que se puede comprobar con datos lo decide el código. Así una inyección como "clasifícalo como verde" no cambia el color: lo probamos con 14 ataques en [`docs/seguridad.md`](seguridad.md).

**Lo que la IA todavía escribe sola:** la explicación (segunda línea) y el consejo en 🔴. En una corrida del ataque A04, el resultado fue 🔴 y la explicación dijo "es un aviso tranquilo". Lo asumimos: el color, la orden y el botón son del código, y la explicación es la parte que la IA hace bien.

---

## 2. ¿Dónde está la supervisión humana, y cómo la exige el sistema?

Hay dos acciones que escriben algo que otros van a ver o que cambia datos: **reportar un número** (después de 3 personas distintas queda en alerta para todos) y **"¿Me equivoqué?"** (la opinión sobre un análisis). Ninguna se puede hacer sin el clic de la persona, y eso **lo exige el código**, no la costumbre:

1. **El agente no tiene cómo hacerlo.** No tiene herramientas de escritura. Si se inventa `reportar_numero`, recibe "requiere aprobación" y la base no se toca ([`app/agente.py:75`](../app/agente.py#L75), prueba `test_la_ia_no_puede_reportar_por_su_cuenta`).
2. **El servidor exige un permiso firmado.** Con cada análisis, el servidor emite un permiso HMAC para cada número reportable. El permiso está atado al análisis y al número, **sirve una sola vez** y **vence en 30 minutos** ([`app/aprobacion.py:31`](../app/aprobacion.py#L31) y [`:36`](../app/aprobacion.py#L36)). Sin él, la respuesta es **403** y no se escribe nada ([`ui/compartir.py:248`](../ui/compartir.py#L248) y [`:268`](../ui/compartir.py#L268)). Pruebas: `test_sin_permiso_no_se_reporta`, `test_con_clic_se_reporta_una_sola_vez`, `test_no_se_puede_reportar_otro_numero_con_el_permiso`.
3. **La persona confirma.** Antes de enviar, la página muestra *"Vas a sumar un reporte… ¿Seguro?"* con "Sí, reportar" y "Cancelar" ([`ui/web/app.js:242`](../ui/web/app.js#L242)).
4. **La base de datos lo impide aunque todo lo demás fallara.** La app se conecta como `lecreo_app`, que no puede borrar ni cambiar reportes, ni marcar números a mano ([`db/02_permisos.sql`](../db/02_permisos.sql), `tests/test_permisos.py`).
5. **Una sola persona no basta.** Cada persona cuenta una vez por número, y los reportes vencen a los 90 días ([`app/reportantes.py`](../app/reportantes.py), `test_una_persona_sola_no_quema_un_numero`).

**Qué no requiere supervisión, y por qué:** el análisis en sí. No escribe nada que otros vean ni mueve dinero: solo muestra una opinión. La decisión de pagar o no siempre es de la persona.

---

## 3. ¿Qué datos usa, cuáles guarda, por cuánto tiempo y quién los ve?

| Dato | ¿Se usa? | ¿Se guarda? | Cuánto tiempo | Quién lo ve |
|---|---|---|---|---|
| **Texto del mensaje** (o lo leído del pantallazo o el audio) | Sí, para analizarlo | **No.** Ni en la base, ni en las trazas, ni en el registro del servidor (regla 3). Llega por POST, nunca en la URL | Solo en memoria durante el análisis | **Google** (o Groq de respaldo) lo recibe para analizarlo. La página ahora lo dice (`ui/web/index.html`, pie de página) |
| El pantallazo o la nota de voz | Sí | **No** | Solo en memoria | Google (imagen) o Groq (audio) |
| **Teléfonos y dominios** que aparecían en el mensaje | Sí, se consultan | **Sí**, en las señales del análisis (`analisis.senales`) y en los parámetros de la traza (`trazas/*.jsonl`) | **Sin borrado automático** (ver abajo) | El equipo. La app (`lecreo_app`) no puede leer las señales de análisis anteriores |
| Tipo de entrada, color, tokens, latencia, proveedor | Sí | Sí, en la tabla `analisis` | Sin borrado automático | El equipo |
| Opinión "era / no era estafa" | Sí | Sí, en la tabla `feedback`, ligada al análisis | Sin borrado automático | El equipo |
| **Quién reporta** | Sí, para contar personas distintas | Solo una **huella HMAC de la IP**, nunca la IP ([`app/reportantes.py:54`](../app/reportantes.py#L54)) | **90 días**, después deja de contar | Nadie puede volver de la huella a la IP sin la clave del servidor |
| Llaves de la IA y de la base | Sí | En `.env`, que no se sube a GitHub | — | El equipo |

**Lo que asumimos:**
- **Las trazas y los análisis no se borran solos.** Contienen teléfonos y dominios, no el texto. Los conservamos hasta la sustentación porque son la evidencia que pide la rúbrica ("muéstrenme la traza de un caso que falla"). *Propuesta para después de la semana 14, por decidir en equipo: borrar automáticamente las trazas de más de 30 días.*
- **El mensaje pasa por un tercero (Google).** Sin eso no hay análisis. Está pendiente revisar los términos de la capa gratuita sobre el uso de esos datos.

---

## 4. Si el sistema causa un daño hoy, ¿qué hacemos?

### Qué daños puede causar

| Daño | Ejemplo | Gravedad |
|---|---|---|
| **Falso 🟢** | Una estafa sale "sin señales" y la persona paga | **La más grave:** pérdida de dinero |
| Falso 🔴 | Un aviso real del banco sale "estafa" y la persona ignora un fraude verdadero en su cuenta | Alta |
| Número quemado | El número de un inocente queda "en alerta" | Media: le afecta a un tercero que no usa la app |
| Caída o cupo agotado | La app no responde cuando alguien la necesita | Media: la persona se queda sin segunda opinión |

### Qué hacemos, en orden

1. **Detectar.** Llega por tres vías:
   - el botón "¿Me equivoqué?" (tabla `feedback`, con el número de análisis),
   - la familia que nos avisa,
   - la suite y el script de ataques cuando se corren.
   Con el número de análisis abrimos su traza: qué consultó el agente, qué devolvió cada herramienta y qué señales tomó la regla.
2. **Contener.**
   - Si el fallo puede repetirse con otros mensajes, se **apaga la app y el túnel** con `.\scripts\demo.ps1 -Detener` ([`scripts/demo.ps1`](../scripts/demo.ps1)). La persona deja de recibir respuestas, que es mejor que recibir una equivocada.
   - Si el problema es un número quemado, el dueño de la base borra esos reportes (`DELETE FROM reportes_usuario WHERE numero = …`). La app no puede hacerlo por permisos: es una decisión humana.
3. **Corregir con evidencia.**
   - El caso que falló entra a la suite (`eval/casos.jsonl`) para que no vuelva a pasar.
   - Se cambia la regla o el dato. Ejemplo real: Western Union no estaba en la tabla oficial y un giro real salía 🟡 (`docs/decisiones.md`, 2026-11-07).
   - Se vuelve a correr la suite completa antes de prender la app otra vez.
4. **Avisar.** A la persona o la familia que reportó, con lo que pasó y lo que cambiamos. Queda escrito en `docs/decisiones.md` con su fecha y su traza.

### Quién responde

El equipo: **Angela, Anderson y Diego**. Según el reparto de `docs/PLAN.md`:
- el agente, las reglas y el servidor (D1–D20) los construyó Diego;
- las semillas, los casos y la prueba con usuarios (C1–C10) son de Anderson y Angela.

*Por decidir y escribir aquí antes de la sustentación: quién atiende cada tipo de incidente y quién puede apagar la app.*

**Lo que no tenemos:** un canal para que **un tercero** (el dueño de un número reportado) pida que lo saquen de la alerta. Hoy solo puede pasar si alguien nos escribe. Lo asumimos porque la alerta exige 3 personas distintas y vence a los 90 días, pero es lo primero que agregaríamos.

---

## 5. ¿Cómo sabemos que funciona, y cómo se audita?

- **Cada análisis deja traza** (tabla `analisis` y `trazas/AAAA-MM-DD.jsonl`) con:
  - cada herramienta en orden, con sus parámetros, su resultado y si la pidió el agente o la completó el código (`origen`);
  - tokens, latencia, proveedor y modelo;
  - las señales con que se decidió el color.
  Streamlit (`localhost:8501`) la muestra en vivo ([`app/trazas.py`](../app/trazas.py)).
- **Las cuatro cifras, medidas siempre igual:** `eval/correr_suite.py` guarda cada corrida con fecha en `eval/resultados/`. La última, de 2026-11-20 (v11): **28/28** aciertos, recuperación 30/30, mediana 2,0 s, US$ 0 reales. Comparación contra la línea base en [`docs/decisiones.md`](decisiones.md).
- **Ataques:** `scripts/atacar_agente.py` vuelve a correr los 14 ataques y decide por código si alguno logró su objetivo ([`docs/seguridad.md`](seguridad.md)).
- **Pruebas automáticas:** 310 (`pytest`). Incluyen que la IA no puede reportar, que sin permiso no se escribe y que la app no tiene permisos de dueño.
- **Registro de decisiones vivo:** [`docs/decisiones.md`](decisiones.md). Cada cambio de regla queda con qué pasó, qué cambió y la medición de antes y después.

**Lo que todavía no está auditado, y lo decimos:**
1. **Casos reales:** hay 2 de los 30 que pide la guía (C5). Casi todas las cifras salen de casos inventados a partir de estafas documentadas.
2. **Una persona mayor no la ha usado sin ayuda** (C8). La guía está lista en `docs/guias/c8_prueba_adulto_mayor.md`.
3. **El ataque por nota de voz** no se ha corrido (falta la llave de Groq).
