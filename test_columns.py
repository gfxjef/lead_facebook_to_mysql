#!/usr/bin/env python3
"""
Script para probar la creación de columnas en fb_leads
"""
import os
import pymysql
from dotenv import load_dotenv
from modules.lead_consolidator import ensure_procesado_column

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def test_column_creation():
    """Prueba la creación de columnas procesado y enviado"""
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
            # Verificar si la tabla existe
            cur.execute("SHOW TABLES LIKE 'fb_leads'")
            if not cur.fetchone():
                print("❌ Tabla fb_leads no existe. Ejecuta la app primero para crear la tabla.")
                return False
            
            print("✅ Tabla fb_leads existe")
            
            # Mostrar columnas actuales
            cur.execute("SHOW COLUMNS FROM fb_leads")
            columns = cur.fetchall()
            print("\n📋 Columnas actuales en fb_leads:")
            for col in columns:
                print(f"  - {col['Field']} ({col['Type']})")
            
            # Verificar y crear columnas
            print("\n🔧 Ejecutando ensure_procesado_column...")
            ensure_procesado_column(cur, conn)
            
            # Mostrar columnas después
            cur.execute("SHOW COLUMNS FROM fb_leads")
            columns_after = cur.fetchall()
            print("\n📋 Columnas después de la verificación:")
            for col in columns_after:
                print(f"  - {col['Field']} ({col['Type']})")
            
            # Verificar específicamente las columnas
            column_names = [col['Field'] for col in columns_after]
            procesado_exists = 'procesado' in column_names
            enviado_exists = 'enviado' in column_names
            
            print(f"\n✅ Columna 'procesado': {'SÍ' if procesado_exists else 'NO'}")
            print(f"✅ Columna 'enviado': {'SÍ' if enviado_exists else 'NO'}")
            
            if procesado_exists and enviado_exists:
                print("\n🎉 ¡Todas las columnas están correctamente creadas!")
                return True
            else:
                print("\n❌ Faltan columnas por crear")
                return False
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando creación de columnas en fb_leads...")
    test_column_creation()