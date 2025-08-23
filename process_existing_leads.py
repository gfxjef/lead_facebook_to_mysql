#!/usr/bin/env python3
"""
Script independiente para procesar leads existentes en fb_leads 
y consolidarlos en expokossodo_registros + expokossodo_registro_eventos

Este script:
1. Busca todos los leads con enviado=0 en fb_leads
2. Los procesa usando la lógica de consolidación existente
3. Los marca como enviado=1 al finalizar
4. Muestra estadísticas del procesamiento
"""

import os
import pymysql
from dotenv import load_dotenv
from datetime import datetime
from modules.lead_consolidator import consolidate_lead_to_registros, ensure_procesado_column

# Cargar variables de entorno
load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def get_pending_leads(cursor):
    """Obtiene todos los leads pendientes de enviar (enviado=0)"""
    try:
        cursor.execute("""
            SELECT id, ad_name, adset_name, sala, email, full_name, phone
            FROM fb_leads 
            WHERE enviado = 0 
            ORDER BY created_time ASC
        """)
        leads = cursor.fetchall()
        print(f"📋 Encontrados {len(leads)} leads pendientes de procesar")
        return leads
    except Exception as e:
        print(f"❌ Error obteniendo leads pendientes: {e}")
        return []

def process_leads_batch(leads, cursor, connection):
    """Procesa un lote de leads"""
    processed = 0
    errors = 0
    
    for i, lead in enumerate(leads, 1):
        try:
            print(f"\n🔄 Procesando lead {i}/{len(leads)} - ID: {lead['id']}")
            print(f"   📧 Email: {lead['email']}")
            print(f"   👤 Nombre: {lead['full_name']}")
            print(f"   🎯 Anuncio: {lead['ad_name'][:50]}...")
            
            # Preparar datos del lead
            lead_data = {
                'id': lead['id'],
                'ad_name': lead['ad_name'],
                'adset_name': lead['adset_name'], 
                'sala': lead['sala'],
                'email': lead['email'],
                'full_name': lead['full_name'],
                'phone_number': lead['phone'],
                'cargo': '',  # No disponible en leads históricos
                'empresa': ''  # No disponible en leads históricos
            }
            
            # Consolidar usando la lógica existente
            success = consolidate_lead_to_registros(lead_data, cursor, connection)
            
            if success:
                processed += 1
                print(f"   ✅ Lead {lead['id']} procesado exitosamente")
            else:
                errors += 1
                print(f"   ❌ Error procesando lead {lead['id']}")
                
        except Exception as e:
            errors += 1
            print(f"   💥 Excepción procesando lead {lead['id']}: {e}")
            continue
    
    return processed, errors

def main():
    """Función principal del script"""
    start_time = datetime.now()
    print("🚀 INICIANDO PROCESAMIENTO DE LEADS EXISTENTES")
    print("=" * 60)
    print(f"⏰ Hora de inicio: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print("❌ Error: Variables de entorno de base de datos no configuradas")
        return
    
    try:
        # Conectar a la base de datos
        print(f"🔗 Conectando a {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False,  # Usaremos transacciones manuales
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        
        with connection.cursor() as cursor:
            print("✅ Conexión establecida")
            
            # Verificar que las columnas existan
            print("🔧 Verificando columnas necesarias...")
            ensure_procesado_column(cursor, connection)
            
            # Obtener leads pendientes
            print("📋 Buscando leads pendientes...")
            leads = get_pending_leads(cursor)
            
            if not leads:
                print("✅ No hay leads pendientes de procesar")
                return
            
            # Confirmar procesamiento
            print(f"\n⚠️  Se van a procesar {len(leads)} leads")
            response = input("¿Continuar? (s/N): ").lower().strip()
            if response != 's':
                print("❌ Procesamiento cancelado por el usuario")
                return
            
            # Procesar leads
            print(f"\n🔄 Iniciando procesamiento de {len(leads)} leads...")
            processed, errors = process_leads_batch(leads, cursor, connection)
            
            # Estadísticas finales
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "=" * 60)
            print("📊 RESUMEN DEL PROCESAMIENTO")
            print("=" * 60)
            print(f"✅ Leads procesados exitosamente: {processed}")
            print(f"❌ Leads con errores: {errors}")
            print(f"📋 Total leads: {len(leads)}")
            print(f"⏱️  Tiempo total: {duration.total_seconds():.2f} segundos")
            print(f"⚡ Promedio: {duration.total_seconds()/len(leads):.2f} seg/lead")
            
            if processed > 0:
                print(f"\n🎉 ¡Procesamiento completado!")
                print(f"   - {processed} registros creados en expokossodo_registros")
                print(f"   - {processed} relaciones creadas en expokossodo_registro_eventos")
                print(f"   - Slots ocupados actualizados en expokossodo_eventos")
            
        connection.close()
        print("🔐 Conexión cerrada")
        
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        return

if __name__ == "__main__":
    main()