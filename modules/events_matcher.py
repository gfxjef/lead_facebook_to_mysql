import re
from datetime import datetime

def normalize_by_45_char(title):
    """Limpia sufijos y corta a 40 caracteres."""
    if not title: return ""
    cleaned = re.sub(r'\s*-\s*copia.*$', '', title.strip(), flags=re.IGNORECASE)
    return cleaned[:40].lower()

def normalize_by_colon(title):
    """Toma el texto antes de los dos puntos y lo limpia."""
    if not title: return ""
    if ':' in title:
        return title.split(':')[0].strip().lower()
    return None

def find_event_id(ad_name, adset_name, sala, all_events):
    """
    Encuentra el ID del evento correspondiente usando la lógica de dos pasos.
    Retorna el event_id o None si no se encuentra.
    """
    date_map = {'dia 1': '2025-09-02', 'dia 2': '2025-09-03', 'dia 3': '2025-09-04'}
    sala_map = {'s1': 'sala1', 's2': 'sala2', 's3': 'sala3', 's4': 'sala4'}
    
    target_date = date_map.get(adset_name.lower() if adset_name else '')
    target_sala = sala_map.get(sala.lower() if sala else '')
    
    if not target_date or not target_sala:
        print(f"[WARNING] No se pudo mapear Día o Sala para: {adset_name} / {sala}")
        return None
    
    # Intento #1: 40 Caracteres
    normalized_lead_title_45 = normalize_by_45_char(ad_name)
    for event in all_events:
        event_date = event['fecha'].strftime('%Y-%m-%d') if event['fecha'] else ''
        if (target_date == event_date and
            target_sala == event['sala'] and
            normalized_lead_title_45 == normalize_by_45_char(event['titulo_charla'])):
            print(f"[MATCH] Evento encontrado por método 40 caracteres: ID {event['id']}")
            return event['id']
    
    # Intento #2: Dos Puntos
    normalized_lead_title_colon = normalize_by_colon(ad_name)
    if normalized_lead_title_colon:
        for event in all_events:
            normalized_event_title_colon = normalize_by_colon(event['titulo_charla'])
            event_date = event['fecha'].strftime('%Y-%m-%d') if event['fecha'] else ''
            if (normalized_event_title_colon and
                target_date == event_date and
                target_sala == event['sala'] and
                normalized_lead_title_colon == normalized_event_title_colon):
                print(f"[MATCH] Evento encontrado por método dos puntos: ID {event['id']}")
                return event['id']
    
    print(f"[WARNING] No se encontró evento para: {ad_name}")
    return None