# ============================================================
#  config/firebase_config.py  –  Versión Web
#  Lee credenciales desde variable de entorno (para Railway)
# ============================================================

import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "AIzaSyCznNcCoQ7XGMwSOpLHJX-ISBTSxhNA-UA")
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"


def inicializar_firebase():
    if not firebase_admin._apps:
        # En Railway: usa variable de entorno FIREBASE_CREDENTIALS (JSON como string)
        # En local:   usa el archivo serviceAccountKey.json
        creds_json = os.environ.get("FIREBASE_CREDENTIALS")
        if creds_json:
            cred_dict = json.loads(creds_json)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate("config/serviceAccountKey.json")

        firebase_admin.initialize_app(cred)
        print("[Firebase] Conexión inicializada.")


def obtener_firestore():
    return firestore.client()
