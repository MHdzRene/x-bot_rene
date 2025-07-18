import json
import os
from datetime import datetime

USAGE_FILE = 'x_api_usage.json'

# Caps mensuales (ajusta según plan)
READ_CAP = 15000  # posts leídos/mes
POST_CAP_USER = 3000  # posts escritos/mes por usuario
POST_CAP_APP = 50000  # posts escritos/mes por app


def _get_month_key():
    now = datetime.now()
    return f"{now.year}-{now.month:02d}"

def load_usage():
    if not os.path.exists(USAGE_FILE):
        return {}
    with open(USAGE_FILE, 'r') as f:
        return json.load(f)

def save_usage(data):
    with open(USAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_current_usage():
    data = load_usage()
    key = _get_month_key()
    return data.get(key, {'read': 0, 'post_user': 0, 'post_app': 0})

def increment_usage(read=0, post_user=0, post_app=0):
    data = load_usage()
    key = _get_month_key()
    usage = data.get(key, {'read': 0, 'post_user': 0, 'post_app': 0})
    usage['read'] += read
    usage['post_user'] += post_user
    usage['post_app'] += post_app
    data[key] = usage
    save_usage(data)

def check_caps(warn_threshold=0.9):
    usage = get_current_usage()
    warnings = []
    if usage['read'] >= READ_CAP:
        raise Exception(f"Read cap mensual alcanzado: {usage['read']} / {READ_CAP}")
    if usage['post_user'] >= POST_CAP_USER:
        raise Exception(f"Post cap usuario mensual alcanzado: {usage['post_user']} / {POST_CAP_USER}")
    if usage['post_app'] >= POST_CAP_APP:
        raise Exception(f"Post cap app mensual alcanzado: {usage['post_app']} / {POST_CAP_APP}")
    # Advertencias si se acerca al límite
    if usage['read'] >= warn_threshold * READ_CAP:
        warnings.append(f"⚠️ Advertencia: Uso de lecturas al {usage['read']}/{READ_CAP} ({100*usage['read']/READ_CAP:.1f}%)")
    if usage['post_user'] >= warn_threshold * POST_CAP_USER:
        warnings.append(f"⚠️ Advertencia: Uso de posts usuario al {usage['post_user']}/{POST_CAP_USER} ({100*usage['post_user']/POST_CAP_USER:.1f}%)")
    if usage['post_app'] >= warn_threshold * POST_CAP_APP:
        warnings.append(f"⚠️ Advertencia: Uso de posts app al {usage['post_app']}/{POST_CAP_APP} ({100*usage['post_app']/POST_CAP_APP:.1f}%)")
    for w in warnings:
        print(w)
    return usage
