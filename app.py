# ============================================================
#  app.py  –  Servidor Flask principal
#  ChuquiWeb – Marketplace de Importadoras
# ============================================================

from dotenv import load_dotenv
load_dotenv()   # carga el .env local (en Railway usa las vars de entorno directas)

import os
from flask import Flask

# ── Inicializar Firebase ANTES de importar cualquier módulo ──
from config.firebase_config import inicializar_firebase
inicializar_firebase()

# ── Blueprints ───────────────────────────────────────────────
from venta.rutas_usuarios    import usuarios_bp
from venta.rutas_tiendas     import tiendas_bp
from venta.rutas_marketplace import marketplace_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "chuquiweb_secret_2025")

    # Registrar blueprints
    app.register_blueprint(marketplace_bp)    # "/"
    app.register_blueprint(usuarios_bp)       # "/login", "/admin/usuarios"
    app.register_blueprint(tiendas_bp)        # "/admin/tiendas"

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)