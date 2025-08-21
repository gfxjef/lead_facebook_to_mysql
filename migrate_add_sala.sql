-- Script de migración para agregar columna 'sala' y procesar datos existentes
-- Ejecutar este script si ya tienes datos en la tabla fb_leads

-- 1. Agregar la columna 'sala' si no existe
ALTER TABLE fb_leads ADD COLUMN IF NOT EXISTS sala VARCHAR(10) NULL;

-- 2. Crear índice para la nueva columna
CREATE INDEX IF NOT EXISTS idx_sala ON fb_leads(sala);

-- 3. Actualizar registros existentes extrayendo la sala del ad_name
UPDATE fb_leads 
SET 
    sala = CASE 
        WHEN ad_name REGEXP '^S[0-9]+\\s*-\\s*' THEN 
            SUBSTRING_INDEX(ad_name, ' - ', 1)
        ELSE NULL 
    END,
    ad_name = CASE 
        WHEN ad_name REGEXP '^S[0-9]+\\s*-\\s*' THEN 
            TRIM(SUBSTRING(ad_name, LOCATE(' - ', ad_name) + 3))
        ELSE ad_name 
    END
WHERE ad_name IS NOT NULL 
AND (sala IS NULL OR sala = '');

-- 4. Mostrar ejemplo de los datos actualizados
SELECT 
    id,
    sala,
    ad_name,
    created_time
FROM fb_leads 
WHERE sala IS NOT NULL 
ORDER BY created_time DESC 
LIMIT 10;

-- 5. Estadísticas de la migración
SELECT 
    COUNT(*) as total_leads,
    COUNT(sala) as leads_with_sala,
    COUNT(*) - COUNT(sala) as leads_without_sala
FROM fb_leads;