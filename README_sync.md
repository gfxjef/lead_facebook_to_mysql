# Sincronización Histórica de Leads

## Descripción

El archivo `sync_historical_leads.py` permite traer todos los leads históricos de un formulario de Facebook y guardarlos en la misma base de datos MySQL que usa el webhook.

## Uso

### Requisitos
- Tener configurado el archivo `.env` con todas las variables necesarias
- Haber instalado las dependencias: `pip install -r requirements.txt`

### Comandos disponibles

**1. Sincronizar todos los leads históricos:**
```bash
python sync_historical_leads.py --form_id 2559418034391311
```

**2. Sincronizar por rango de fechas:**
```bash
python sync_historical_leads.py --form_id 2559418034391311 --since 2025-08-01 --until 2025-08-21
```

**3. Ajustar tamaño de página:**
```bash
python sync_historical_leads.py --form_id 2559418034391311 --limit 200
```

### Parámetros

- `--form_id`: (Requerido) ID del formulario de Facebook
- `--since`: (Opcional) Fecha desde (formato: YYYY-MM-DD o timestamp unix)
- `--until`: (Opcional) Fecha hasta (formato: YYYY-MM-DD o timestamp unix) 
- `--limit`: (Opcional) Leads por página (default: 100, máximo recomendado: 500)

## Características

✅ **Reutiliza el mismo código** que el webhook (funciones de app.py)
✅ **Idempotente** - no duplica leads existentes
✅ **Paginación automática** - maneja grandes volúmenes de datos
✅ **Rate limiting** - respeta límites de API de Facebook
✅ **Procesamiento completo** - obtiene nombres de campaña, adset, anuncio y extrae sala
✅ **Manejo de errores** - continúa procesando aunque algunos leads fallen
✅ **Progreso en tiempo real** - muestra estadísticas mientras procesa

## Variables necesarias en .env

```env
# Token de página para obtener leads
PAGE_TOKEN=EAAP7R8vzYY4...

# Token de marketing para obtener nombres
MKT_TOKEN=EAAP7R8vzYY4...

# ID de la página
PAGE_ID=142158129158183

# Configuración MySQL
DB_HOST=tu_host
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_PORT=3306
```

## Ejemplo de ejecución

```bash
$ python sync_historical_leads.py --form_id 2559418034391311 --since 2025-08-01

Iniciando sincronización histórica para form_id: 2559418034391311
Desde: 2025-08-01
Límite por página: 100
--------------------------------------------------
Obteniendo página 1...
  → 100 leads en esta página
Procesando lead 1: 1234567890123456 (2025-08-21T17:57:05+0000)
  ✅ Guardado exitosamente
Procesando lead 2: 1234567890123457 (2025-08-21T16:45:12+0000)
  ✅ Guardado exitosamente
...
Paginación completada. Total de páginas: 3
--------------------------------------------------
Sincronización completada:
  📊 Procesados: 250
  ✅ Guardados: 248
  ❌ Errores: 2
🎉 Sincronización completada sin errores!
```

## Datos procesados

El script procesa exactamente la misma información que el webhook:
- ✅ Datos del lead (nombre, email, teléfono)
- ✅ IDs originales (campaign_id, adset_id, ad_id)
- ✅ Nombres obtenidos via Marketing API (campaign_name, adset_name, ad_name)
- ✅ Sala extraída automáticamente del nombre del anuncio
- ✅ JSON completo del lead en columna raw_json

## Recomendaciones

- **Primera vez:** Ejecuta sin filtros de fecha para obtener todo el histórico
- **Mantenimiento:** Usa `--since` para sincronizaciones incrementales
- **Gran volumen:** Usa `--limit 200` para páginas más grandes
- **Rate limits:** Si Facebook devuelve error 429, el script tiene un delay automático