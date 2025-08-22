import re
import time

def generate_qr_text(nombres, numero, cargo, empresa):
    """
    Genera el texto para el código QR según el formato:
    {3_LETRAS}|{DNI}|{CARGO}|{EMPRESA}|{TIMESTAMP}
    """
    # Limpiar nombre para obtener solo letras
    nombres_clean = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', '', nombres.upper())
    tres_letras = nombres_clean[:3].ljust(3, 'X')
    
    # Limpiar campos reemplazando pipe | con guión -
    numero_clean = str(numero).replace('|', '-') if numero else ''
    cargo_clean = str(cargo).replace('|', '-') if cargo else ''
    empresa_clean = str(empresa).replace('|', '-') if empresa else ''
    
    # Generar timestamp
    timestamp = int(time.time())
    
    # Formato final
    qr_text = f"{tres_letras}|{numero_clean}|{cargo_clean}|{empresa_clean}|{timestamp}"
    
    return qr_text