-- Script SQL para verificar columnas en fb_leads
USE atusalud_kossomet;

-- Mostrar estructura de la tabla fb_leads
DESCRIBE fb_leads;

-- Verificar si existe la columna 'enviado'
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'fb_leads' 
AND COLUMN_NAME IN ('procesado', 'enviado');

-- Si no existe la columna 'enviado', crearla:
-- ALTER TABLE fb_leads ADD COLUMN enviado TINYINT(1) DEFAULT 0;