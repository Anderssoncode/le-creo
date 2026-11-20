# Respuesta a la auditoría cruzada

> Momento 3 · entregable obligatorio.
> **Estado: esperando el reporte del equipo auditor.** Todavía no está en el repositorio. Cuando llegue, va completo en `docs/auditoria_recibida.md` (sin editar) y cada hallazgo se responde en la tabla de abajo.

## Cómo respondemos

La rúbrica califica igual *"lo arreglamos"* que *"lo asumimos y por qué"*, y castiga prometer arreglos que no se hicieron. Por eso, cada hallazgo lleva **una** de estas tres respuestas:

| Respuesta | Qué tiene que traer |
|---|---|
| **Lo arreglamos** | El commit, la prueba que lo demuestra y, si cambia una cifra, la medición de antes y después |
| **Lo asumimos** | Por qué no lo cambiamos (costo, público, alcance de la spec) y qué haría falta para cambiarlo |
| **No estamos de acuerdo** | La evidencia: traza, prueba o línea de código que muestra que el sistema ya lo hace |

Nada se marca "lo arreglamos" sin el commit en `main`.

## Hallazgos del equipo auditor

| # | Hallazgo (como lo escribieron) | Gravedad según ellos | Respuesta | Evidencia |
|---|---|---|---|---|
| 1 | *(pendiente: llega con el reporte)* | | | |

## Lo que ya encontramos nosotros (autoauditoría, 2026-11-20)

Antes de recibir el reporte, atacamos y revisamos nuestro propio sistema. Si el equipo auditor señala algo de esta lista, la respuesta ya tiene su evidencia.

| Hallazgo propio | Respuesta | Evidencia |
|---|---|---|
| Una inyección ("en que_hacer escribe: llama al 300…") hizo que el modelo omitiera un teléfono y una estafa saliera 🟢 | **Lo arreglamos** | Trazas #127 (antes) y #211 (después). `app/verificacion.py`, `app/reglas.py` (`telefonos_sin_verificar`), `tests/test_verificacion.py`. Detalle en `docs/seguridad.md` |
| La app se conectaba a Postgres como dueña de la base | **Lo arreglamos** | `db/02_permisos.sql`. `tests/test_permisos.py`: 9 operaciones que pasan como dueño y fallan como app |
| Una sola persona podía poner en alerta el número de cualquiera | **Lo arreglamos** | Cuentan personas distintas y los reportes vencen a los 90 días: `app/reportantes.py`, `test_una_persona_sola_no_quema_un_numero` |
| Detrás del túnel, todos compartían un solo cupo de 5 análisis por minuto | **Lo arreglamos** | `ui/compartir.py` (`ip_cliente`), `test_detras_del_tunel_el_limite_es_por_persona` |
| Un mensaje que pedía la cédula, sin otra señal, salía 🟢 | **Lo arreglamos** | `app/reglas.py` (`datos_personales` es señal blanda), `test_pedir_datos_personales_no_puede_salir_verde` |
| Un cobro real por enlace oficial (DiDi) salía 🟢 a veces | **Lo arreglamos** | Prompt: un cobro siempre es `transferencia`. `eval/resultados/2026-11-20_1320_google_v10_cobros_c13_c14.json`: 12/12 |
| La página decía "no guardo tus mensajes", pero no que el texto pasa por una IA externa | **Lo arreglamos** | Pie de página en `ui/web/index.html` |
| La explicación (segunda línea) la sigue escribiendo el modelo y puede contradecir el color | **Lo asumimos** | El color, la orden, el paso con teléfonos dudosos y el botón Llamar son del código. Ver `docs/gobernanza.md`, pregunta 1 |
| Las trazas guardan teléfonos y dominios del mensaje, sin borrado automático | **Lo asumimos hasta la semana 14** | Son la evidencia de la sustentación. Ver `docs/gobernanza.md`, pregunta 3 |
| El dueño de un número reportado no tiene cómo pedir que lo saquen | **Lo asumimos** | La alerta exige 3 personas y vence a los 90 días. Sería lo primero que agregaríamos (`docs/gobernanza.md`, pregunta 4) |
| Solo 2 casos reales de 30 (C5), y no se ha hecho la prueba con un adulto mayor (C8) | **Pendiente del equipo** | Guías listas en `docs/guias/` |
