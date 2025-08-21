import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# Prueba de conexión al servidor MySQL remoto
try:
    print("Conectando al servidor MySQL remoto...")
    conn = pymysql.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        charset="utf8mb4"
    )
    
    print(f"✅ Conectado exitosamente a: {os.environ.get('DB_HOST')}")
    print(f"   Base de datos: {os.environ.get('DB_NAME')}")
    
    with conn.cursor() as cursor:
        # Verificar si la tabla existe
        cursor.execute("SHOW TABLES LIKE 'fb_leads'")
        result = cursor.fetchone()
        
        if result:
            print("✅ La tabla 'fb_leads' ya existe")
            cursor.execute("SELECT COUNT(*) FROM fb_leads")
            count = cursor.fetchone()[0]
            print(f"   Registros actuales: {count}")
        else:
            print("⚠️ La tabla 'fb_leads' no existe (se creará al recibir el primer lead)")
            
            # Opción para crear la tabla ahora
            respuesta = input("\n¿Deseas crear la tabla ahora? (s/n): ")
            if respuesta.lower() == 's':
                cursor.execute("""
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
                conn.commit()
                print("✅ Tabla 'fb_leads' creada exitosamente")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("\nVerifica en tu .env:")
    print(f"  DB_HOST = {os.environ.get('DB_HOST')}")
    print(f"  DB_NAME = {os.environ.get('DB_NAME')}")
    print(f"  DB_USER = {os.environ.get('DB_USER')}")
    print(f"  DB_PORT = {os.environ.get('DB_PORT')}")