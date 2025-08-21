# Facebook Leads to MySQL Webhook

Sistema automatizado para capturar leads de formularios de Facebook y almacenarlos en MySQL con respaldo local.

## Características

- ✅ Webhook para recibir leads de Facebook en tiempo real
- ✅ Validación de firma X-Hub-Signature-256
- ✅ Almacenamiento en MySQL remoto con idempotencia
- ✅ Respaldo local en archivos JSON
- ✅ Creación automática de carpeta de respaldos
- ✅ Creación automática de tabla en base de datos

## Requisitos

- Python 3.8+
- MySQL 5.7+
- Cuenta de Facebook Developer
- Página de Facebook con formularios de leads

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/gfxjef/lead_facebook_to_mysql.git
cd lead_facebook_to_mysql
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
Crear archivo `.env` con:
```env
# Base de datos MySQL
DB_HOST=tu_servidor_mysql
DB_NAME=tu_base_datos
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_PORT=3306

# Facebook API
FB_APP_SECRET=tu_app_secret
FB_PAGE_ACCESS_TOKEN=tu_page_access_token
WEBHOOK_VERIFY_TOKEN=tu_token_verificacion
```

## Uso

1. Iniciar el servidor:
```bash
python app.py
```

2. Para producción con ngrok (desarrollo local):
```bash
ngrok http 8000
```

3. Configurar webhook en Facebook:
   - URL: `https://tu-dominio.com/facebook/webhook`
   - Token de verificación: el mismo que en `WEBHOOK_VERIFY_TOKEN`
   - Suscribir al evento: `leadgen`

## Estructura del Proyecto

```
leads_facebook_to_mysql/
│
├── app.py                 # Servidor Flask principal
├── test_connection.py     # Script para probar conexión MySQL
├── requirements.txt       # Dependencias Python
├── create_table.sql      # Script SQL para crear tabla
├── .env                  # Variables de entorno (no incluido en git)
├── .gitignore           # Archivos ignorados por git
└── Leads_expokossodo/   # Carpeta para respaldos JSON (creada automáticamente)
```

## Endpoints

- `GET /` - Estado del servidor
- `GET /health` - Health check
- `GET /facebook/webhook` - Verificación de webhook (Facebook)
- `POST /facebook/webhook` - Recepción de leads

## Base de Datos

La tabla `fb_leads` se crea automáticamente con la siguiente estructura:

- `id` - ID único del lead (de Facebook)
- `form_id` - ID del formulario
- `page_id` - ID de la página
- `campaign_id` - ID de campaña publicitaria
- `adset_id` - ID del conjunto de anuncios
- `ad_id` - ID del anuncio
- `full_name` - Nombre completo
- `email` - Correo electrónico
- `phone` - Teléfono
- `created_time` - Fecha/hora de creación
- `raw_json` - JSON completo del lead
- `ingested_at` - Timestamp de inserción

## Seguridad

- ✅ Validación de firma HMAC-SHA256
- ✅ Variables sensibles en archivo `.env`
- ✅ `.gitignore` configurado para no subir credenciales
- ✅ Inserción idempotente (evita duplicados)

## Testing

Probar conexión a base de datos:
```bash
python test_connection.py
```

## Licencia

MIT