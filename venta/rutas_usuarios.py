"""
venta/rutas_usuarios.py
Capa de vista (Flask): rutas de autenticación y gestión de usuarios.
"""

import os
from flask import (
    Blueprint, request, jsonify,
    render_template, session, redirect, url_for
)
from servi_user.servicio_usuario import ServicioUsuario

usuarios_bp = Blueprint("auth", __name__)
servicio    = ServicioUsuario()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def requiere_admin():
    """Redirige si no hay sesión activa con rol admin."""
    if not session.get("uid"):
        return redirect(url_for("auth.login"))
    if not servicio.tiene_acceso_admin(session.get("rol", "")):
        return redirect(url_for("marketplace.inicio"))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN — Email / Password
# ─────────────────────────────────────────────────────────────────────────────
@usuarios_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("uid"):
        return _redirigir_segun_rol(session.get("rol", ""))

    if request.method == "POST":
        data     = request.get_json()
        email    = data.get("email", "")
        password = data.get("password", "")

        ok, msg, usuario = servicio.login(email, password)
        if not ok:
            return jsonify({"error": msg}), 401

        _guardar_sesion(usuario)

        if not servicio.tiene_acceso_admin(usuario.rol):
            return jsonify({
                "redirect": url_for("marketplace.inicio"),
                "mensaje":  msg,
            })

        return jsonify({"redirect": url_for("auth.panel_usuarios"), "mensaje": msg})

    # ── GET: pasar config pública de Firebase al template ──
    return render_template(
        "login.html",
        firebase_api_key     = os.environ.get("FIREBASE_API_KEY", ""),
        firebase_auth_domain = os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
        firebase_project_id  = os.environ.get("FIREBASE_PROJECT_ID", ""),
    )


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN — Google (recibe idToken desde el cliente JS)
# ─────────────────────────────────────────────────────────────────────────────
@usuarios_bp.route("/login/google", methods=["POST"])
def login_google():
    data     = request.get_json()
    id_token = data.get("idToken", "")

    ok, msg, usuario = servicio.login_con_google(id_token)
    if not ok:
        return jsonify({"error": msg}), 401

    _guardar_sesion(usuario)

    if not servicio.tiene_acceso_admin(usuario.rol):
        return jsonify({
            "redirect": url_for("marketplace.inicio"),
            "mensaje":  msg,
        })

    return jsonify({"redirect": url_for("auth.panel_usuarios"), "mensaje": msg})


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────
@usuarios_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────────────────────
# PANEL DE USUARIOS (solo admin)
# ─────────────────────────────────────────────────────────────────────────────
@usuarios_bp.route("/admin/usuarios")
def panel_usuarios():
    guard = requiere_admin()
    if guard:
        return guard
    usuarios = servicio.listar_usuarios()
    return render_template("usuarios.html", usuarios=usuarios, roles=ServicioUsuario.ROLES_VALIDOS)


# ─────────────────────────────────────────────────────────────────────────────
# API REST — Usuarios
# ─────────────────────────────────────────────────────────────────────────────

@usuarios_bp.route("/api/usuarios", methods=["GET"])
def api_listar():
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    return jsonify([u.to_dict() for u in servicio.listar_usuarios()])


@usuarios_bp.route("/api/usuarios", methods=["POST"])
def api_crear():
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    ok, msg, usuario = servicio.crear_usuario(
        nombre   = data.get("nombre", ""),
        email    = data.get("email", ""),
        password = data.get("password", ""),
        rol      = data.get("rol", "cliente"),
    )
    if ok:
        return jsonify({"mensaje": msg, "usuario": usuario.to_dict()}), 201
    return jsonify({"error": msg}), 400


@usuarios_bp.route("/api/usuarios/<uid>", methods=["PUT"])
def api_editar(uid):
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    ok, msg = servicio.editar_usuario(
        uid      = uid,
        nombre   = data.get("nombre"),
        email    = data.get("email"),
        password = data.get("password") or None,
        rol      = data.get("rol"),
        activo   = data.get("activo"),
    )
    if ok:
        return jsonify({"mensaje": msg})
    return jsonify({"error": msg}), 400


@usuarios_bp.route("/api/usuarios/<uid>/desactivar", methods=["PATCH"])
def api_desactivar(uid):
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    ok, msg = servicio.desactivar_usuario(uid)
    return jsonify({"mensaje": msg}) if ok else (jsonify({"error": msg}), 400)


@usuarios_bp.route("/api/usuarios/<uid>/activar", methods=["PATCH"])
def api_activar(uid):
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    ok, msg = servicio.activar_usuario(uid)
    return jsonify({"mensaje": msg}) if ok else (jsonify({"error": msg}), 400)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNOS
# ─────────────────────────────────────────────────────────────────────────────
def _guardar_sesion(usuario) -> None:
    session["uid"]    = usuario.uid
    session["nombre"] = usuario.nombre
    session["email"]  = usuario.email
    session["rol"]    = usuario.rol


def _redirigir_segun_rol(rol: str):
    if servicio.tiene_acceso_admin(rol):
        return redirect(url_for("auth.panel_usuarios"))
    return redirect(url_for("marketplace.inicio"))