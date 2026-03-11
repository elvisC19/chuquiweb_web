from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for

from servi_tienda.servicio_tienda import ServicioTienda

tiendas_bp = Blueprint("tiendas", __name__)
servicio = ServicioTienda()


# ─────────────────────────────────────────────────────────────────────────────
# Middleware: proteger rutas que requieren sesión admin
# ─────────────────────────────────────────────────────────────────────────────
def requiere_admin():
    if not session.get("uid") or session.get("rol") != "admin":
        return redirect(url_for("auth.login"))
    return None


# ─────────────────────────────────────────────────────────────────────────────
# VISTA PRINCIPAL: Panel de Tiendas (solo admin)
# ─────────────────────────────────────────────────────────────────────────────
@tiendas_bp.route("/admin/tiendas")
def panel_tiendas():
    guard = requiere_admin()
    if guard:
        return guard
    tiendas = servicio.listar_tiendas()
    return render_template(
        "tiendas.html",
        tiendas=tiendas,
        categorias=ServicioTienda.CATEGORIAS_VALIDAS,
        paises=ServicioTienda.PAISES_ORIGEN,
        planes=ServicioTienda.PLANES,
    )


# ─────────────────────────────────────────────────────────────────────────────
# API REST (JSON) — consumida por el JS del template
# ─────────────────────────────────────────────────────────────────────────────

@tiendas_bp.route("/api/tiendas", methods=["GET"])
def api_listar_tiendas():
    """Lista todas las tiendas."""
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    tiendas = servicio.listar_tiendas()
    return jsonify([t.to_dict() for t in tiendas])


@tiendas_bp.route("/api/tiendas", methods=["POST"])
def api_crear_tienda():
    """Crea una nueva tienda."""
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    ok, msg, tienda = servicio.crear_tienda(
        nombre=data.get("nombre", ""),
        subdominio=data.get("subdominio", ""),
        logo_url=data.get("logo_url", ""),
        descripcion=data.get("descripcion", ""),
        categoria=data.get("categoria", ""),
        pais_origen=data.get("pais_origen", ""),
        email_contacto=data.get("email_contacto", ""),
        telefono=data.get("telefono", ""),
        direccion=data.get("direccion", ""),
        plan=data.get("plan", "basico"),
        uid_propietario=data.get("uid_propietario", session.get("uid", "")),
        banner_url=data.get("banner_url", ""),
        sitio_web=data.get("sitio_web", ""),
        descripcion_larga=data.get("descripcion_larga", ""),
    )

    if ok:
        return jsonify({"mensaje": msg, "tienda": tienda.to_dict()}), 201
    return jsonify({"error": msg}), 400


@tiendas_bp.route("/api/tiendas/<tienda_id>", methods=["GET"])
def api_obtener_tienda(tienda_id):
    """Obtiene una tienda por ID."""
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    tienda = servicio.obtener_tienda(tienda_id)
    if tienda:
        return jsonify(tienda.to_dict())
    return jsonify({"error": "Tienda no encontrada"}), 404


@tiendas_bp.route("/api/tiendas/<tienda_id>", methods=["PUT"])
def api_actualizar_tienda(tienda_id):
    """Actualiza campos de una tienda."""
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    data = request.get_json()
    ok, msg = servicio.actualizar_tienda(tienda_id, data)
    if ok:
        return jsonify({"mensaje": msg})
    return jsonify({"error": msg}), 400


@tiendas_bp.route("/api/tiendas/<tienda_id>/desactivar", methods=["PATCH"])
def api_desactivar_tienda(tienda_id):
    """Desactiva (baja lógica) una tienda."""
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    ok, msg = servicio.desactivar_tienda(tienda_id)
    if ok:
        return jsonify({"mensaje": msg})
    return jsonify({"error": msg}), 400


@tiendas_bp.route("/api/tiendas/<tienda_id>/activar", methods=["PATCH"])
def api_activar_tienda(tienda_id):
    """Reactiva una tienda desactivada."""
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    ok, msg = servicio.activar_tienda(tienda_id)
    if ok:
        return jsonify({"mensaje": msg})
    return jsonify({"error": msg}), 400


@tiendas_bp.route("/api/tiendas/<tienda_id>/plan", methods=["PATCH"])
def api_cambiar_plan(tienda_id):
    """Cambia el plan de suscripción de una tienda."""
    guard = requiere_admin()
    if guard:
        return jsonify({"error": "No autorizado"}), 401
    data = request.get_json()
    ok, msg = servicio.cambiar_plan(tienda_id, data.get("plan", ""))
    if ok:
        return jsonify({"mensaje": msg})
    return jsonify({"error": msg}), 400