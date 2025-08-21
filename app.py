import os
import hmac
import hashlib
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
import requests
import pymysql

load_dotenv()

FB_APP_SECRET = os.environ.get("FB_APP_SECRET", "").encode()
PAGE_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
VERIFY_TOKEN = os.environ.get("WEBHOOK_VERIFY_TOKEN", "mi_token_verificacion_123")

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

LEADS_FOLDER = "Leads_expokossodo"

app = Flask(__name__)

def init_app():
    """Inicializa la aplicación creando carpetas necesarias"""
    if not os.path.exists(LEADS_FOLDER):
        os.makedirs(LEADS_FOLDER)
        app.logger.info(f"Carpeta '{LEADS_FOLDER}' creada exitosamente")
    else:
        app.logger.info(f"Carpeta '{LEADS_FOLDER}' ya existe")

def verify_signature(req) -> bool:
    """Valida X-Hub-Signature-256 con el APP_SECRET."""
    sig = req.headers.get("X-Hub-Signature-256", "")
    if not sig.startswith("sha256="):
        return False
    received = sig.split("=", 1)[1]
    digest = hmac.new(FB_APP_SECRET, msg=req.get_data(), digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, digest)

def fetch_lead(lead_id: str) -> dict:
    """Obtiene el lead completo desde Graph API."""
    url = f"https://graph.facebook.com/v20.0/{lead_id}"
    params = {
        "access_token": PAGE_TOKEN,
        "fields": "id,created_time,field_data,ad_id,adset_id,campaign_id,form_id,platform"
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def parse_common_fields(lead_json: dict):
    """Mapea campos comunes desde field_data."""
    fd = lead_json.get("field_data", [])
    field_map = {}
    for f in fd:
        name = f.get("name")
        values = f.get("values") or []
        field_map[name] = values[0] if values else None

    full_name = field_map.get("full_name") or field_map.get("name")
    email = field_map.get("email")
    phone = field_map.get("phone_number") or field_map.get("phone")
    return full_name, email, phone

def save_lead_to_file(lead_json: dict, leadgen_id: str):
    """Guarda el lead en un archivo JSON en la carpeta Leads_expokossodo"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{LEADS_FOLDER}/lead_{leadgen_id}_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(lead_json, f, ensure_ascii=False, indent=2)
    
    app.logger.info(f"Lead guardado en archivo: {filename}")

def save_lead_mysql(lead_json: dict, form_id: int, page_id: int):
    """Inserta lead en MySQL con idempotencia."""
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        app.logger.warning("MySQL no configurado completamente. Solo guardando en archivo.")
        return

    full_name, email, phone = parse_common_fields(lead_json)
    created_time = datetime.fromisoformat(lead_json["created_time"].replace("Z", "+00:00")).astimezone(timezone.utc)
    payload = json.dumps(lead_json, ensure_ascii=False)

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=True,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fb_leads (
                  id BIGINT PRIMARY KEY,
                  form_id BIGINT NOT NULL,
                  page_id BIGINT NOT NULL,
                  campaign_id VARCHAR(64) NULL,
                  adset_id VARCHAR(64) NULL,
                  ad_id VARCHAR(64) NULL,
                  full_name VARCHAR(255) NULL,
                  email VARCHAR(255) NULL,
                  phone VARCHAR(64) NULL,
                  created_time DATETIME NOT NULL,
                  raw_json JSON NOT NULL,
                  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            sql = """
            INSERT INTO fb_leads (id, form_id, page_id, campaign_id, adset_id, ad_id,
                                  full_name, email, phone, created_time, raw_json)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              campaign_id=VALUES(campaign_id),
              adset_id=VALUES(adset_id),
              ad_id=VALUES(ad_id),
              full_name=VALUES(full_name),
              email=VALUES(email),
              phone=VALUES(phone),
              raw_json=VALUES(raw_json);
            """
            cur.execute(sql, (
                int(lead_json["id"]),
                int(form_id),
                int(page_id),
                lead_json.get("campaign_id"),
                lead_json.get("adset_id"),
                lead_json.get("ad_id"),
                full_name,
                email,
                phone,
                created_time.strftime("%Y-%m-%d %H:%M:%S"),
                payload
            ))
        conn.close()
        app.logger.info(f"Lead {lead_json['id']} guardado en MySQL")
    except Exception as e:
        app.logger.exception(f"Error guardando lead en MySQL: {e}")

@app.get("/facebook/webhook")
def verify():
    """Verifica el webhook para Facebook (GET)"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge:
        app.logger.info("Webhook verificado exitosamente")
        return Response(challenge, status=200, mimetype="text/plain")
    
    return "Verification failed", 403

@app.post("/facebook/webhook")
def receive():
    """Recibe los eventos de Facebook (POST)"""
    if FB_APP_SECRET and not verify_signature(request):
        return "Invalid signature", 403

    body = request.get_json(silent=True) or {}
    
    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "leadgen":
                value = change.get("value", {})
                leadgen_id = value.get("leadgen_id")
                form_id = value.get("form_id")
                page_id = value.get("page_id")
                
                app.logger.info(f"Nuevo lead recibido: {leadgen_id}")

                try:
                    lead_json = fetch_lead(leadgen_id)
                    
                    save_lead_to_file(lead_json, leadgen_id)
                    
                    save_lead_mysql(lead_json, form_id, page_id)
                    
                except Exception as e:
                    app.logger.exception(f"Error procesando lead {leadgen_id}: {e}")
                    continue

    return "OK", 200

@app.route("/")
def home():
    """Página de inicio para verificar que el servidor está funcionando"""
    return jsonify({
        "status": "running",
        "webhook_url": "/facebook/webhook",
        "leads_folder": LEADS_FOLDER,
        "folder_exists": os.path.exists(LEADS_FOLDER)
    })

@app.route("/health")
def health():
    """Endpoint de salud para monitoreo"""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    init_app()
    app.run(host="0.0.0.0", port=8000, debug=True)