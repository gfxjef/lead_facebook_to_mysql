#!/usr/bin/env python3
"""
Sincronización histórica de leads de Facebook
============================================

Script independiente para traer todos los leads históricos de un formulario
de Facebook y guardarlos en la misma base de datos MySQL.

Uso:
    python sync_historical_leads.py --form_id 2559418034391311
    python sync_historical_leads.py --form_id 2559418034391311 --since 2025-08-01 --until 2025-08-21
    python sync_historical_leads.py --form_id 2559418034391311 --limit 200

Este script reutiliza las mismas funciones de app.py para mantener consistencia.
"""

import os
import sys
import argparse
import time
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
import requests
import pymysql

# Cargar variables de entorno
load_dotenv()

# Variables de configuración
PAGE_TOKEN = os.environ.get("PAGE_TOKEN", "")
MKT_TOKEN = os.environ.get("MKT_TOKEN", "")
PAGE_ID = os.environ.get("PAGE_ID", "142158129158183")  # ID de tu página

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME") 
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def fetch_lead(lead_id: str) -> dict:
    """Obtiene el lead completo desde Graph API (v23.0)"""
    url = f"https://graph.facebook.com/v23.0/{lead_id}"
    params = {
        "access_token": PAGE_TOKEN,
        "fields": "id,created_time,field_data,ad_id,adset_id,campaign_id,form_id,platform"
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def get_campaign_name(campaign_id: str) -> str:
    """Obtiene el nombre de la campaña desde Facebook Marketing API"""
    if not campaign_id or not MKT_TOKEN:
        return None
    
    try:
        url = f"https://graph.facebook.com/v23.0/{campaign_id}"
        params = {
            "fields": "name",
            "access_token": MKT_TOKEN
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception as e:
        print(f"Warning: Error obteniendo nombre de campaña {campaign_id}: {e}")
        return None

def get_adset_name(adset_id: str) -> str:
    """Obtiene el nombre del adset desde Facebook Marketing API"""
    if not adset_id or not MKT_TOKEN:
        return None
    
    try:
        url = f"https://graph.facebook.com/v23.0/{adset_id}"
        params = {
            "fields": "name",
            "access_token": MKT_TOKEN
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception as e:
        print(f"Warning: Error obteniendo nombre de adset {adset_id}: {e}")
        return None

def get_ad_name(ad_id: str) -> str:
    """Obtiene el nombre del anuncio desde Facebook Marketing API"""
    if not ad_id or not MKT_TOKEN:
        return None
    
    try:
        url = f"https://graph.facebook.com/v23.0/{ad_id}"
        params = {
            "fields": "name",
            "access_token": MKT_TOKEN
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("name")
    except Exception as e:
        print(f"Warning: Error obteniendo nombre de anuncio {ad_id}: {e}")
        return None

def extract_sala_and_clean_name(ad_name: str) -> tuple:
    """
    Extrae la sala del nombre del anuncio y limpia el nombre.
    
    Ejemplos:
    'S3 - De la Microscopía Óptica...' -> ('S3', 'De la Microscopía Óptica...')
    'S1 - Determinación de Vida...' -> ('S1', 'Determinación de Vida...')
    'Nombre sin sala' -> (None, 'Nombre sin sala')
    """
    if not ad_name:
        return None, ad_name
    
    import re
    pattern = r'^(S\d+)\s*-\s*(.+)$'
    match = re.match(pattern, ad_name.strip())
    
    if match:
        sala = match.group(1)  # Ej: "S3"
        clean_name = match.group(2).strip()  # Resto del nombre
        return sala, clean_name
    else:
        return None, ad_name

def parse_common_fields(lead_json: dict):
    """Mapea campos comunes desde field_data"""
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

def save_lead_mysql(lead_json: dict, form_id: int, page_id: int):
    """Inserta lead en MySQL con idempotencia - mismo código que app.py"""
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("MySQL no configurado completamente.")
        return False

    full_name, email, phone = parse_common_fields(lead_json)
    created_time = datetime.fromisoformat(lead_json["created_time"].replace("Z", "+00:00")).astimezone(timezone.utc)
    payload = json.dumps(lead_json, ensure_ascii=False)
    
    # Obtener nombres desde Facebook Marketing API
    campaign_name = get_campaign_name(lead_json.get("campaign_id"))
    adset_name = get_adset_name(lead_json.get("adset_id"))
    ad_name_raw = get_ad_name(lead_json.get("ad_id"))
    
    # Extraer sala y limpiar nombre del anuncio
    sala, ad_name = extract_sala_and_clean_name(ad_name_raw)

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
            # Crear tabla si no existe (mismo schema que app.py)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fb_leads (
                  id BIGINT PRIMARY KEY,
                  form_id BIGINT NOT NULL,
                  page_id BIGINT NOT NULL,
                  campaign_id VARCHAR(64) NULL,
                  adset_id VARCHAR(64) NULL,
                  ad_id VARCHAR(64) NULL,
                  campaign_name VARCHAR(255) NULL,
                  adset_name VARCHAR(255) NULL,
                  ad_name VARCHAR(255) NULL,
                  sala VARCHAR(10) NULL,
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
                                  campaign_name, adset_name, ad_name, sala,
                                  full_name, email, phone, created_time, raw_json)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              campaign_id=VALUES(campaign_id),
              adset_id=VALUES(adset_id),
              ad_id=VALUES(ad_id),
              campaign_name=VALUES(campaign_name),
              adset_name=VALUES(adset_name),
              ad_name=VALUES(ad_name),
              sala=VALUES(sala),
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
                campaign_name,
                adset_name,
                ad_name,
                sala,
                full_name,
                email,
                phone,
                created_time.strftime("%Y-%m-%d %H:%M:%S"),
                payload
            ))
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error guardando lead {lead_json['id']} en MySQL: {e}")
        return False

def fetch_form_leads(form_id: str, since: str = None, until: str = None, limit: int = 100):
    """
    Itera sobre todos los leads de un formulario (paginando).
    Devuelve un generador de diccionarios mínimos: {'id': '...', 'created_time': '...'}.
    """
    base_url = f"https://graph.facebook.com/v23.0/{form_id}/leads"
    params = {
        "access_token": PAGE_TOKEN,
        "limit": limit,
        "fields": "id,created_time"
    }
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    page_count = 0
    while True:
        print(f"Obteniendo página {page_count + 1}...")
        r = requests.get(base_url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        leads_in_page = len(data.get("data", []))
        print(f"  → {leads_in_page} leads en esta página")

        for item in (data.get("data") or []):
            yield item

        # Paginación
        paging = data.get("paging", {})
        next_url = paging.get("next")
        cursors = paging.get("cursors", {})
        after = cursors.get("after")
        
        if next_url and after:
            params["after"] = after
            page_count += 1
            time.sleep(0.5)  # Rate limiting amistoso
        else:
            print(f"Paginación completada. Total de páginas: {page_count + 1}")
            break

def sync_form_leads_to_db(form_id: str, since: str = None, until: str = None, limit: int = 100):
    """
    Recorre TODOS los leads del formulario y los guarda en MySQL.
    Retorna un resumen {'processed': X, 'saved': Y, 'errors': Z}.
    """
    print(f"Iniciando sincronización histórica para form_id: {form_id}")
    if since:
        print(f"Desde: {since}")
    if until:
        print(f"Hasta: {until}")
    print(f"Límite por página: {limit}")
    print("-" * 50)
    
    processed = saved = errors = 0
    
    for minimal in fetch_form_leads(form_id, since=since, until=until, limit=limit):
        processed += 1
        lead_id = minimal.get("id")
        created_time = minimal.get("created_time")
        
        print(f"Procesando lead {processed}: {lead_id} ({created_time})")
        
        try:
            # Obtener lead completo
            full = fetch_lead(lead_id)
            
            # Obtener form_id y page_id
            form_id_full = full.get("form_id") or int(form_id)
            page_id_full = int(PAGE_ID)
            
            # Guardar en base de datos
            if save_lead_mysql(full, form_id_full, page_id_full):
                saved += 1
                print(f"  ✅ Guardado exitosamente")
            else:
                errors += 1
                print(f"  ❌ Error al guardar")
                
        except Exception as e:
            errors += 1
            print(f"  ❌ Error procesando lead {lead_id}: {e}")
            continue

    print("-" * 50)
    print(f"Sincronización completada:")
    print(f"  📊 Procesados: {processed}")
    print(f"  ✅ Guardados: {saved}")
    print(f"  ❌ Errores: {errors}")
    
    return {"processed": processed, "saved": saved, "errors": errors}

def main():
    parser = argparse.ArgumentParser(description="Sincronizar leads históricos de Facebook")
    parser.add_argument("--form_id", required=True, help="ID del formulario de Facebook")
    parser.add_argument("--since", help="Fecha desde (YYYY-MM-DD o timestamp unix)")
    parser.add_argument("--until", help="Fecha hasta (YYYY-MM-DD o timestamp unix)")
    parser.add_argument("--limit", type=int, default=100, help="Leads por página (default: 100)")
    
    args = parser.parse_args()
    
    # Verificar tokens
    if not PAGE_TOKEN:
        print("❌ Error: PAGE_TOKEN no configurado en .env")
        sys.exit(1)
        
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("❌ Error: Configuración de MySQL incompleta en .env")
        sys.exit(1)
    
    # Ejecutar sincronización
    try:
        summary = sync_form_leads_to_db(
            args.form_id, 
            since=args.since, 
            until=args.until, 
            limit=args.limit
        )
        
        if summary["errors"] == 0:
            print("🎉 Sincronización completada sin errores!")
        else:
            print(f"⚠️ Sincronización completada con {summary['errors']} errores")
            
    except Exception as e:
        print(f"❌ Error fatal durante la sincronización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()