-- Mínimo privilegio (Momento 3, hardening S3).
--
-- La app y el agente se conectan como lecreo_app, no como el dueño de la base (lecreo). Solo puede
-- hacer lo que el código necesita; lo demás lo impide Postgres, aunque una inyección o un error
-- llegara a armar una consulta:
--   · lee las tablas de consulta y los reportes,
--   · inserta trazas (analisis), opiniones (feedback) y reportes aprobados (reportes_usuario),
--   · renueva la fecha de un reporte repetido,
--   · NO puede borrar, vaciar, cambiar semillas, crear tablas ni tocar numeros_reportados.
-- Las tareas de administración (cargar semillas, limpiar datos de prueba) usan DATABASE_URL_ADMIN.
--
-- Idempotente: lo corren Docker al crear el volumen y scripts/cargar_semillas.py en cada arranque.
-- La clave es de desarrollo, como la de lecreo en docker-compose.yml; en un servidor real se cambia.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lecreo_app') THEN
    CREATE ROLE lecreo_app LOGIN PASSWORD 'lecreo_app';
  END IF;
END
$$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM lecreo_app;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM lecreo_app;
REVOKE CREATE ON SCHEMA public FROM lecreo_app;

GRANT CONNECT ON DATABASE lecreo TO lecreo_app;
GRANT USAGE ON SCHEMA public TO lecreo_app;

-- Herramientas del agente: solo lectura.
GRANT SELECT ON canales_oficiales, dominios_oficiales, acortadores, numeros_reportados TO lecreo_app;

-- Reportes aprobados con un clic (D14, R3): leer, agregar y renovar la fecha. Nunca borrar.
GRANT SELECT, INSERT ON reportes_usuario TO lecreo_app;
GRANT UPDATE (fecha) ON reportes_usuario TO lecreo_app;

-- Trazas y opiniones: solo agregar. SELECT (id) es para el RETURNING id de la traza.
GRANT INSERT ON analisis, feedback TO lecreo_app;
GRANT SELECT (id) ON analisis TO lecreo_app;
GRANT USAGE ON SEQUENCE analisis_id_seq, feedback_id_seq TO lecreo_app;
