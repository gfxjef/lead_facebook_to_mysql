-- Script de migración para agregar columnas de nombres a tabla existente
-- Ejecutar este script si ya tienes datos en la tabla fb_leads

-- Agregar las nuevas columnas
ALTER TABLE fb_leads ADD COLUMN IF NOT EXISTS campaign_name VARCHAR(255) NULL;
ALTER TABLE fb_leads ADD COLUMN IF NOT EXISTS adset_name VARCHAR(255) NULL;
ALTER TABLE fb_leads ADD COLUMN IF NOT EXISTS ad_name VARCHAR(255) NULL;

-- Agregar índices para mejor performance
CREATE INDEX IF NOT EXISTS idx_campaign_name ON fb_leads(campaign_name);
CREATE INDEX IF NOT EXISTS idx_adset_name ON fb_leads(adset_name);
CREATE INDEX IF NOT EXISTS idx_ad_name ON fb_leads(ad_name);

-- Mostrar estructura actualizada
DESCRIBE fb_leads;