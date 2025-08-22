import json
from datetime import datetime
from modules.events_matcher import find_event_id
from modules.qr_generator import generate_qr_text

def consolidate_lead_to_registros(lead_data, cursor, connection):
    """
    Consolida un lead de Facebook a la tabla expokossodo_registros.
    
    Args:
        lead_data: Diccionario con los datos del lead
        cursor: Cursor de MySQL
        connection: Conexión MySQL para hacer commit
    
    Returns:
        bool: True si se procesó correctamente, False si hubo error
    """
    try:
        # 1. Obtener todos los eventos para el matching
        cursor.execute("SELECT id, titulo_charla, fecha, sala FROM expokossodo_eventos")
        all_events = cursor.fetchall()
        
        # 2. Encontrar el ID del evento correspondiente
        event_id = find_event_id(
            lead_data['ad_name'],
            lead_data['adset_name'],
            lead_data['sala'],
            all_events
        )
        
        if not event_id:
            print(f"[WARNING] No se pudo encontrar evento para lead ID {lead_data['id']}")
            return False
        
        # 3. Verificar si ya existe un registro con este correo
        cursor.execute(
            "SELECT id, eventos_seleccionados FROM expokossodo_registros WHERE correo = %s",
            (lead_data['email'],)
        )
        existing_registro = cursor.fetchone()
        
        if existing_registro:
            # 4a. Si existe, actualizar eventos_seleccionados si es necesario
            eventos_actuales = json.loads(existing_registro['eventos_seleccionados']) if existing_registro['eventos_seleccionados'] else []
            
            if event_id not in eventos_actuales:
                # Agregar el nuevo evento
                eventos_actuales.append(event_id)
                eventos_json = json.dumps(eventos_actuales)
                
                cursor.execute(
                    """UPDATE expokossodo_registros 
                       SET eventos_seleccionados = %s
                       WHERE id = %s""",
                    (eventos_json, existing_registro['id'])
                )
                connection.commit()
                print(f"[UPDATE] Agregado evento {event_id} al registro existente ID {existing_registro['id']}")
            else:
                print(f"[INFO] El evento {event_id} ya está en el registro ID {existing_registro['id']}")
        
        else:
            # 4b. Si no existe, crear nuevo registro
            
            # Generar QR con datos reales
            qr_code = generate_qr_text(
                lead_data['full_name'],
                lead_data['phone_number'] or '',
                lead_data.get('cargo') or '',
                lead_data.get('empresa') or ''
            )
            
            # Preparar datos para inserción
            eventos_json = json.dumps([event_id])
            fecha_actual = datetime.now()
            
            cursor.execute(
                """INSERT INTO expokossodo_registros 
                   (nombres, correo, empresa, cargo, numero, expectativas, 
                    eventos_seleccionados, qr_code, qr_generado_at, 
                    asistencia_general_confirmada, fecha_registro, confirmado)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    lead_data['full_name'],
                    lead_data['email'],
                    lead_data.get('empresa') or '',
                    lead_data.get('cargo') or '',
                    lead_data['phone_number'] or '',
                    '',  # expectativas vacías
                    eventos_json,
                    qr_code,
                    fecha_actual,
                    0,  # asistencia_general_confirmada = false
                    fecha_actual,
                    0   # confirmado = false
                )
            )
            connection.commit()
            print(f"[INSERT] Nuevo registro creado con ID {cursor.lastrowid} para {lead_data['email']}")
        
        # 5. Marcar el lead como procesado y enviado
        cursor.execute(
            "UPDATE fb_leads SET procesado = 1, enviado = 1 WHERE id = %s",
            (lead_data['id'],)
        )
        connection.commit()
        print(f"[SUCCESS] Lead ID {lead_data['id']} marcado como procesado y enviado")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error consolidando lead ID {lead_data['id']}: {e}")
        connection.rollback()
        return False

def ensure_procesado_column(cursor, connection):
    """
    Verifica y crea las columnas 'procesado' y 'enviado' en fb_leads si no existen.
    """
    try:
        # Verificar columna 'procesado'
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'fb_leads' 
            AND COLUMN_NAME = 'procesado'
        """)
        
        if not cursor.fetchone():
            print("[INFO] Agregando columna 'procesado' a tabla fb_leads...")
            cursor.execute("""
                ALTER TABLE fb_leads 
                ADD COLUMN procesado TINYINT(1) DEFAULT 0
            """)
            connection.commit()
            print("[SUCCESS] Columna 'procesado' agregada exitosamente")
        else:
            print("[INFO] Columna 'procesado' ya existe en fb_leads")
        
        # Verificar columna 'enviado'
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'fb_leads' 
            AND COLUMN_NAME = 'enviado'
        """)
        
        if not cursor.fetchone():
            print("[INFO] Agregando columna 'enviado' a tabla fb_leads...")
            cursor.execute("""
                ALTER TABLE fb_leads 
                ADD COLUMN enviado TINYINT(1) DEFAULT 0
            """)
            connection.commit()
            print("[SUCCESS] Columna 'enviado' agregada exitosamente")
        else:
            print("[INFO] Columna 'enviado' ya existe en fb_leads")
            
    except Exception as e:
        print(f"[ERROR] Error verificando/creando columnas: {e}")