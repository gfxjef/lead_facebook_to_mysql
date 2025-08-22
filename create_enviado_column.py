#!/usr/bin/env python3
"""
Script para crear la columna 'enviado' en la tabla fb_leads
"""
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME") 
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def create_enviado_column():
    """Crea la columna 'enviado' en fb_leads"""
    try:
        print(f"🔗 Conectando a {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        
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
                print("❌ Tabla fb_leads no existe.")
                return False
            
            print("✅ Tabla fb_leads encontrada")
            
            # Verificar columnas actuales
            cur.execute("SHOW COLUMNS FROM fb_leads")
            columns = cur.fetchall()
            column_names = [col['Field'] for col in columns]
            
            print(f"📋 Columnas actuales: {', '.join(column_names)}")
            
            # Verificar si ya existe la columna 'enviado'
            if 'enviado' in column_names:
                print("✅ La columna 'enviado' ya existe")
                return True
            
            # Crear la columna 'enviado'
            print("🔧 Creando columna 'enviado'...")
            cur.execute("""
                ALTER TABLE fb_leads 
                ADD COLUMN enviado TINYINT(1) DEFAULT 0
            """)
            
            print("✅ Columna 'enviado' creada exitosamente")
            
            # Verificar que se creó
            cur.execute("SHOW COLUMNS FROM fb_leads WHERE Field = 'enviado'")
            result = cur.fetchone()
            if result:
                print(f"✅ Verificación exitosa: {result['Field']} ({result['Type']})")
                return True
            else:
                print("❌ Error: No se pudo verificar la columna")
                return False
        
        conn.close()
        print("🔐 Conexión cerrada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Creando columna 'enviado' en fb_leads...")
    success = create_enviado_column()
    if success:
        print("🎉 ¡Columna 'enviado' lista!")
    else:
        print("💥 Error al crear la columna")