# Guion de la presentación final (Momento 3)

**Archivo de la presentación:** `docs/presentacion_final.html`. Se abre en Chrome, con F para pantalla completa.

**La historia:** Doña Carmen recibe un mensaje falso de Nequi. Ese mismo mensaje recorre toda la presentación:
1. Qué hace la app con él.
2. Cómo un estafador intentaría engañar a la app.
3. Qué tan bien funciona, con cifras y con los fallos.

**El orden sigue la rúbrica**, para que el profe califique mientras hablamos:

| Bloque | Quién | Diapositivas | Criterios de la rúbrica |
|---|---|---|---|
| Producto | Angela | 1–6 | Funciona, alcance y necesidad (25 pts) |
| Seguridad y gobernanza | Anderson | 7–11 | 20 + 20 pts |
| Medición y cierre | Diego | 12–15 | 15 pts y "qué harían distinto" |

## Controles

| Tecla | Qué hace |
|---|---|
| → o espacio | Avanza |
| ← | Retrocede |
| **N** | Muestra las notas del que habla: lo que hay que decir en cada diapositiva |
| **M** | Cambia entre la versión de 12 y la de 6 minutos |
| **T** | Cronómetro, que empieza al pasar de la portada |
| **F** | Pantalla completa |
| **Fin** | Apéndice "Dónde está cada cosa", para las preguntas |
| Clic | Derecha avanza, izquierda retrocede |

## Tiempo

La página del curso **no publica un tiempo exacto** para la final. En el Momento 2 fueron 6 minutos. Hay **dos versiones en el mismo archivo**, con el mismo diseño. Cada una trae sus propias notas (tecla N):

| Versión | Cómo se abre | Diapositivas |
|---|---|---|
| **12 min** (completa) | `presentacion_final.html` | Las 15, más el apéndice |
| **6 min** (unos 5:40) | `presentacion_final.html?modo=6`, o la tecla **M** en cualquier momento | 10, más el apéndice |

**La tecla M cambia de versión sin perder la diapositiva en la que van.** Si el profe recorta el tiempo a mitad de camino, presionen M y sigan.

**Reparto de la versión de 6 minutos** (unos 2 minutos por persona):

| Quién | Diapositivas | Tiempo |
|---|---|---|
| Angela | Portada (10 s) · El mensaje (25 s) · **Demo con un voluntario (60 s)** · La IA lee, el código decide (25 s) | 2:00 |
| Anderson | Tríada (25 s) · **A04 con sus trazas (50 s)** · La línea de la supervisión humana (40 s) | 1:55 |
| Diego | Las 4 cifras (45 s) · Los fallos y lo que falta (35 s) · Cierre (25 s) | 1:45 |

**Qué se salta, y dónde queda dicho:**
- **Spec contra producto (diapositiva 6):** el cambio de Telegram a WhatsApp lo dice Angela en la diapositiva 5.
- **Tres toques (3):** se ve en la demo.
- **Los 14 ataques (8):** Anderson los resume en una frase en A04.
- **Hardening (10):** Anderson nombra los permisos mínimos en gobernanza.
- **Lo que falta (14):** Diego lo dice en la diapositiva de los fallos.

**Pregunten al empezar cuánto tiempo hay** y escojan la versión.

**Para abrir la de 6 minutos en Chrome:** el atajo es abrir la de 12 y presionar **M**. También pueden escribir la ruta completa en la barra de direcciones y agregar `?modo=6` al final:

```
file:///C:/Users/juand/Electiva/le-creo-anderson/docs/presentacion_final.html?modo=6
```

## Antes de entrar (30 min antes)

1. **Docker Desktop abierto.** Después corran `.\scripts\demo.ps1`, que levanta la base, la app (8600), Streamlit (8501) y el túnel, y muestra la URL para el celular.
2. **QR de la demo:** en la diapositiva 4, peguen esa URL en el campo y presionen Enter. Se genera el QR y queda guardado para ese navegador.
3. **Prueben una vez desde un celular** con el mensaje de Doña Carmen:
   > Nequi: tu cuenta será bloqueada hoy por actividad inusual. Para evitarlo comunícate ya con la línea de seguridad 300 000 0042.

   Debe salir 🔴.
4. **Streamlit abierto en otra pestaña:** `localhost:8501`, para mostrar la traza en vivo.
5. **Plan B si falla internet o el túnel:** Diego lo corre en el portátil (`localhost:8600`) y el voluntario escribe en el portátil.

## Lo que dice cada uno

Las notas completas, con los tiempos, están en la presentación: tecla **N**. Esto es lo esencial:

### Angela: el producto (diapositivas 1–6)

1. **Portada.** Quiénes somos y la frase: *una segunda opinión antes de pagar.*
2. **El mensaje.**
   - Doña Carmen es un personaje ilustrativo.
   - *Las estafas atacan la prisa y el miedo, no la tecnología.*
3. **Tres toques.**
   - Compartir → pantalla roja → "Por qué".
   - **Límite que encontramos:** Android no comparte texto. Para texto es Copiar y "Pegar y revisar".
4. **Demo con alguien del público.**
   - La rúbrica da el puntaje máximo si la usa alguien ajeno al equipo.
   - **No le expliquen nada.** Diego muestra la traza en Streamlit mientras tanto.
5. **La IA lee, el código decide.**
   - Por qué hace falta un LLM: el truco cambia de palabras, y hay pantallazos y audios.
   - Qué nunca toca: el color, los números, el botón Llamar y las escrituras.
6. **Spec contra producto.** Qué cambió y por qué: Telegram costaba $5.000 y el profe criticó que un mayor no abre otra página.

### Anderson: seguridad y gobernanza (diapositivas 7–11)

7. **Tríada.**
   - El atacante es el estafador.
   - **Cerramos la salida, en código:** el agente no tiene red, no escribe y nunca abre enlaces.
8. **14 ataques.** Trece fallaron. *Una nos ganó.*
9. **A04, con trazas.**
   - #127 🟢 → arreglo 1 → #171 🟢 otra vez → arreglo 2 → #211 🔴.
   - **La frase:** *el prompt decía "no obedezcas" y obedeció igual; lo que funcionó fue arquitectura.*
10. **Hardening: antes y después.** Permisos mínimos (9 operaciones destructivas fallan), aprobación, reportes y límite por persona.
11. **Gobernanza.**
    - **"Muéstrenme la línea":** `ui/compartir.py:248`. Sin permiso firmado → 403.
    - Si causamos un daño: detectar, contener, corregir y avisar.

### Diego: medición y cierre (diapositivas 12–15)

12. **Las 4 cifras contra la semana 10.**
    - Decir el porqué de cada cambio.
    - **Ser honesto con la latencia:** parte fue Google ese día.
13. **Los fallos con su traza.** De ahí salió *sin certeza no hay verde; el amarillo explica, no acusa.*
14. **Lo que todavía no sabemos.** Solo 2 de 30 mensajes reales; falta la prueba con un adulto mayor y el ataque por nota de voz.
15. **Cierre.**
    - Qué haríamos distinto desde la semana 1.
    - *La IA lee. El código decide. La persona aprueba. Doña Carmen no llamó a ese número.*

## Preguntas probables: quién responde

**La rúbrica castiga que uno solo responda todo.** Cada uno toma las suyas:

| Si preguntan… | Responde | Qué mostrar |
|---|---|---|
| ¿Es lo de la spec de la semana 4? | Angela | Diapositiva 6 y `docs/decisiones.md` §9 |
| Que alguien la use ahora | Angela | Diapositiva 4 (QR) |
| ¿Por qué necesita un LLM? | Angela | Diapositiva 5 |
| Muéstrenme el ataque y qué pasó | Anderson | Diapositiva 9, `docs/seguridad.md` §3 |
| ¿Qué pata de la tríada cerraron y por qué? | Anderson | La salida: la pata 2 no se puede quitar y la 1 ya es mínima |
| Muéstrenme la línea de la supervisión humana | Anderson | `ui/compartir.py:248`, `app/aprobacion.py:36` |
| Si su sistema causa un daño hoy, ¿qué hacen? | Anderson | `docs/gobernanza.md` §4 |
| ¿Cómo están sus cifras contra la semana 10? | Diego | Diapositiva 12 |
| Muéstrenme la traza de un caso que falla | Diego | Streamlit, o la traza #127 en `docs/evidencia/s1_ataques_2026-11-20_1400_antes.json` |
| Explíquenme esta función | Quien la hizo | Apéndice (tecla Fin) |
| ¿Qué harían distinto desde la semana 1? | Diego | Diapositiva 15 |
| ¿La suite no está "entrenada" para dar 100 %? | Diego | **Sí, y lo decimos:** se usó para corregir. Por eso la cifra que generaliza es la de mensajes reales, y hoy son 2 |
| ¿Por qué no tienen la respuesta a la auditoría? | Anderson | Ver la nota de abajo |

## ⚠️ Antes de presentar: la auditoría cruzada

`docs/respuesta_auditoria.md` dice **"esperando el reporte del equipo auditor"**. Es un entregable **obligatorio**:
- **Si ya les llegó el reporte:** respóndanlo hallazgo por hallazgo antes de entrar. *"Lo asumimos y por qué"* vale igual que *"lo arreglamos"*.
- **Si no les llegó:** díganlo con claridad y muestren la autoauditoría, que ya tiene 11 hallazgos con evidencia.
