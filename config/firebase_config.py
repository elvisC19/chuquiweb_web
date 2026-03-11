import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

FIREBASE_API_KEY  = os.environ.get("FIREBASE_API_KEY", "")
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"


def inicializar_firebase():
    """Inicializa Firebase Admin SDK una sola vez (patrón singleton)."""
    if not firebase_admin._apps:
        creds_json = os.environ.get("FIREBASE_CREDENTIALS")
        if creds_json:
            # Railway: credenciales como JSON string en variable de entorno
            cred_dict = json.loads(creds_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # Local: archivo serviceAccountKey.json
            cred = credentials.Certificate("config/serviceAccountKey.json")

        firebase_admin.initialize_app(cred)
        print("[Firebase] Conexión inicializada.")


def obtener_firestore():
    """Función original — se mantiene para compatibilidad."""
    inicializar_firebase()
    return firestore.client()


def get_firestore_client():
    """Alias requerido por los módulos de repositorio."""
    inicializar_firebase()
    return firestore.client()