CREATE TABLE IF NOT EXISTS canales_oficiales (
  id            SERIAL PRIMARY KEY,
  entidad       TEXT NOT NULL,
  sector        TEXT NOT NULL,          -- banco, billetera, mensajeria, gobierno, otro
  canales       TEXT NOT NULL,          -- cómo contacta de verdad
  nunca_pide    TEXT NOT NULL,          -- lo que la entidad nunca pide
  fuente_url    TEXT NOT NULL,          -- página oficial donde se verificó
  verificado_en DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS dominios_oficiales (
  dominio  TEXT PRIMARY KEY,            -- ej: bancolombia.com
  entidad  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS acortadores (
  dominio TEXT PRIMARY KEY              -- ej: bit.ly
);

CREATE TABLE IF NOT EXISTS numeros_reportados (
  numero          TEXT PRIMARY KEY,     -- formato +57XXXXXXXXXX
  reportes        INT  NOT NULL DEFAULT 0,
  ultimo_reporte  DATE,
  origen          TEXT NOT NULL         -- semilla_ficticia (las filas 'usuario' antiguas ya no cuentan)
);

-- Reportes aprobados por personas: uno por persona y número (R3). Así 3 reportes son
-- 3 personas distintas y no 3 clics de la misma. Vencen (REPORTES_VIGENCIA_DIAS, 90 por defecto):
-- un número reciclado por el operador no queda quemado para siempre.
CREATE TABLE IF NOT EXISTS reportes_usuario (
  numero      TEXT NOT NULL,            -- formato +57XXXXXXXXXX
  reportante  TEXT NOT NULL,            -- huella HMAC de la IP (app/reportantes.py), nunca la IP
  fecha       DATE NOT NULL DEFAULT CURRENT_DATE,
  PRIMARY KEY (numero, reportante)
);

CREATE TABLE IF NOT EXISTS analisis (   -- SIN texto original (decisión 6)
  id           SERIAL PRIMARY KEY,
  fecha        TIMESTAMPTZ DEFAULT now(),
  tipo_entrada TEXT,                    -- texto | imagen | audio
  semaforo     TEXT,                    -- rojo | amarillo | verde | rechazo | error
  senales      JSONB,
  proveedor    TEXT,
  modelo       TEXT,
  tokens_in    INT,
  tokens_out   INT,
  latencia_ms  INT,
  iteraciones  INT,
  ok           BOOLEAN
);

CREATE TABLE IF NOT EXISTS feedback (   -- F2: el usuario corrige
  id          SERIAL PRIMARY KEY,
  analisis_id INT REFERENCES analisis(id),
  usuario_dice TEXT,                    -- "era_estafa" | "no_era_estafa"
  fecha       TIMESTAMPTZ DEFAULT now()
);
