-- Script para crear la tabla fb_leads en MySQL
-- Esta tabla almacena los leads de Facebook con idempotencia por ID

CREATE TABLE IF NOT EXISTS fb_leads (
  id BIGINT PRIMARY KEY,                -- leadgen_id de Facebook (único)
  form_id BIGINT NOT NULL,              -- ID del formulario de Facebook
  page_id BIGINT NOT NULL,              -- ID de la página de Facebook
  campaign_id VARCHAR(64) NULL,         -- ID de la campaña publicitaria
  adset_id VARCHAR(64) NULL,            -- ID del conjunto de anuncios
  ad_id VARCHAR(64) NULL,               -- ID del anuncio
  full_name VARCHAR(255) NULL,          -- Nombre completo del lead
  email VARCHAR(255) NULL,              -- Email del lead
  phone VARCHAR(64) NULL,               -- Teléfono del lead
  created_time DATETIME NOT NULL,       -- Fecha/hora de creación del lead
  raw_json JSON NOT NULL,               -- JSON completo del lead para referencia
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Fecha/hora de inserción en BD
);

-- Índices adicionales para búsquedas comunes
CREATE INDEX idx_form_id ON fb_leads(form_id);
CREATE INDEX idx_created_time ON fb_leads(created_time);
CREATE INDEX idx_email ON fb_leads(email);