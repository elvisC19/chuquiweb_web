"""
venta/rutas_marketplace.py
Blueprint del marketplace público de ChuquiWeb.
Accesible por clientes, importadoras y visitantes sin sesión.
"""

from flask import Blueprint, render_template, session

marketplace_bp = Blueprint("marketplace", __name__)


@marketplace_bp.route("/")
def inicio():
    """
    Página principal del marketplace.
    Muestra tiendas activas, productos destacados y categorías.
    Cualquier usuario (incluso sin sesión) puede acceder.
    """
    usuario_nombre = session.get("nombre", "")
    usuario_rol    = session.get("rol", "")

    # TODO: cargar tiendas activas con ServicioTienda cuando esté listo
    # from servi_tienda.servicio_tienda import ServicioTienda
    # tiendas = ServicioTienda().listar_activas()

    return render_template(
        "marketplace/inicio.html",
        usuario_nombre=usuario_nombre,
        usuario_rol=usuario_rol,
    )