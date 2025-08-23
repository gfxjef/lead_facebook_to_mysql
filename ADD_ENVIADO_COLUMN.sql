-- =====================================================
-- SCRIPT PARA CREAR LA COLUMNA 'enviado' EN fb_leads
-- =====================================================
-- Ejecuta este SQL en tu base de datos MySQL

USE atusalud_kossomet;

-- Verificar columnas actuales
SELECT 'COLUMNAS ACTUALES EN fb_leads:' AS info;
SHOW COLUMNS FROM fb_leads;

-- Verificar si la columna 'enviado' ya existe
SELECT 'VERIFICANDO SI EXISTE COLUMNA enviado:' AS info;
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'atusalud_kossomet'
AND TABLE_NAME = 'fb_leads' 
AND COLUMN_NAME = 'enviado';

-- Crear la columna 'enviado' si no existe
-- (Si ya existe, MySQL mostrará un error que puedes ignorar)
ALTER TABLE fb_leads 
ADD COLUMN enviado TINYINT(1) DEFAULT 0;

-- Verificar que se creó correctamente
SELECT 'VERIFICACION FINAL:' AS info;
SHOW COLUMNS FROM fb_leads WHERE Field IN ('procesado', 'enviado');

-- Opcional: Crear índice para mejor rendimiento
CREATE INDEX idx_enviado ON fb_leads(enviado);

SELECT 'SCRIPT COMPLETADO EXITOSAMENTE!' AS resultado;