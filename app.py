# ============================================================
#  app.py  –  Servidor Flask principal
#  ChuquiWeb – Marketplace de Importadoras
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from config.firebase_config import inicializar_firebase, obtener_firestore
from reposi_user.repositorio_usuario import RepositorioUsuario
from servi_user.servicio_usuario import ServicioUsuario
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chuquiweb_secret_2025")

# ── Inicializar Firebase ──────────────────────────────────
inicializar_firebase()
db = obtener_firestore()
repositorio = RepositorioUsuario(db)
servicio = ServicioUsuario(repositorio)


# ── Decorador: requiere sesión activa ────────────────────
def login_requerido(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "uid" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ════════════════════════════════════════════════════════════
#  RUTAS
# ════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if "uid" in session:
        return redirect(url_for("usuarios"))
    return redirect(url_for("login"))


# ── LOGIN ─────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        exito, mensaje, usuario = servicio.login(email, password)
        if exito:
            session["uid"]    = usuario.uid
            session["nombre"] = usuario.nombre
            session["rol"]    = usuario.rol
            return redirect(url_for("usuarios"))
        else:
            error = mensaje

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── GESTIÓN DE USUARIOS ───────────────────────────────────

@app.route("/usuarios")
@login_requerido
def usuarios():
    lista = servicio.listar_usuarios()
    return render_template(
        "usuarios.html",
        usuarios=lista,
        usuario_actual_uid=session.get("uid"),
        nombre_actual=session.get("nombre"),
        rol_actual=session.get("rol"),
    )


@app.route("/usuarios/alta", methods=["POST"])
@login_requerido
def alta_usuario():
    nombre   = request.form.get("nombre", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    rol      = request.form.get("rol", "cliente")

    exito, mensaje = servicio.alta_usuario(nombre, email, password, rol)
    return jsonify({"exito": exito, "mensaje": mensaje})


@app.route("/usuarios/baja/<uid>", methods=["POST"])
@login_requerido
def baja_usuario(uid):
    if uid == session.get("uid"):
        return jsonify({"exito": False, "mensaje": "No puedes darte de baja a ti mismo."})

    exito, mensaje = servicio.baja_usuario(uid, permanente=False)
    return jsonify({"exito": exito, "mensaje": mensaje})


# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
