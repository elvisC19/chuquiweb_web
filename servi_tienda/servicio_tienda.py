import re
import unicodedata
from datetime import datetime
from typing import Optional

from tienda.modelo_tienda import Tienda
from reposi_tienda.repositorio_tienda import RepositorioTienda


class ServicioTienda:
    """
    Capa de servicio: lógica de negocio para la gestión de tiendas.
    Valida, transforma y orquesta operaciones sobre las tiendas.
    """

    CATEGORIAS_VALIDAS = [
        "Electrónica",
        "Ropa y Moda",
        "Alimentos y Bebidas",
        "Hogar y Decoración",
        "Juguetes",
        "Herramientas",
        "Cosméticos",
        "Automotriz",
        "Deportes",
        "Otros",
    ]

    PAISES_ORIGEN = [
        "China", "Brasil", "Argentina", "EE.UU.", "Alemania",
        "Japón", "Corea del Sur", "India", "México", "España", "Otro",
    ]

    PLANES = ["basico", "premium"]

    def __init__(self):
        self.repo = RepositorioTienda()

    # ─────────────────────────────────────────────
    # ALTA DE TIENDA
    # ─────────────────────────────────────────────
    def crear_tienda(
        self,
        nombre: str,
        subdominio: str,
        logo_url: str,
        descripcion: str,
        categoria: str,
        pais_origen: str,
        email_contacto: str,
        telefono: str,
        direccion: str,
        plan: str,
        uid_propietario: str,
        banner_url: str = "",
        sitio_web: str = "",
        descripcion_larga: str = "",
    ) -> tuple[bool, str, Optional[Tienda]]:
        """
        Crea una nueva tienda. Retorna (éxito, mensaje, tienda_creada).
        """
        # ── Validaciones ──
        ok, msg = self._validar_datos(
            nombre, subdominio, logo_url, descripcion,
            categoria, pais_origen, email_contacto,
            telefono, direccion, plan,
        )
        if not ok:
            return False, msg, None

        # ── Subdominio único ──
        subdominio_slug = self._slugify(subdominio)
        if not self.repo.subdominio_disponible(subdominio_slug):
            return False, f"El subdominio '{subdominio_slug}' ya está en uso.", None

        # ── Construcción del objeto ──
        tienda_id = self.repo.generar_id()
        tienda = Tienda(
            tienda_id=tienda_id,
            nombre=nombre.strip(),
            subdominio=subdominio_slug,
            logo_url=logo_url.strip(),
            descripcion=descripcion.strip(),
            categoria=categoria,
            pais_origen=pais_origen,
            email_contacto=email_contacto.strip().lower(),
            telefono=telefono.strip(),
            direccion=direccion.strip(),
            plan=plan,
            activo=True,
            uid_propietario=uid_propietario,
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            banner_url=banner_url.strip() or None,
            sitio_web=sitio_web.strip() or None,
            descripcion_larga=descripcion_larga.strip() or None,
        )

        try:
            tienda_guardada = self.repo.crear_tienda(tienda)
            return True, "Tienda creada exitosamente.", tienda_guardada
        except Exception as e:
            return False, f"Error al guardar en Firebase: {str(e)}", None

    # ─────────────────────────────────────────────
    # BAJA LÓGICA
    # ─────────────────────────────────────────────
    def desactivar_tienda(self, tienda_id: str) -> tuple[bool, str]:
        """Desactiva una tienda sin eliminarla."""
        tienda = self.repo.obtener_por_id(tienda_id)
        if not tienda:
            return False, "Tienda no encontrada."
        if not tienda.activo:
            return False, "La tienda ya está desactivada."
        ok = self.repo.cambiar_estado(tienda_id, False)
        return (True, "Tienda desactivada correctamente.") if ok else (False, "Error al desactivar.")

    def activar_tienda(self, tienda_id: str) -> tuple[bool, str]:
        """Reactiva una tienda previamente desactivada."""
        tienda = self.repo.obtener_por_id(tienda_id)
        if not tienda:
            return False, "Tienda no encontrada."
        if tienda.activo:
            return False, "La tienda ya está activa."
        ok = self.repo.cambiar_estado(tienda_id, True)
        return (True, "Tienda activada correctamente.") if ok else (False, "Error al activar.")

    # ─────────────────────────────────────────────
    # ACTUALIZACIÓN
    # ─────────────────────────────────────────────
    def actualizar_tienda(
        self, tienda_id: str, campos: dict
    ) -> tuple[bool, str]:
        """Actualiza campos de una tienda existente."""
        tienda = self.repo.obtener_por_id(tienda_id)
        if not tienda:
            return False, "Tienda no encontrada."

        # Si cambia subdominio, validar que esté libre
        if "subdominio" in campos:
            nuevo_slug = self._slugify(campos["subdominio"])
            if not self.repo.subdominio_disponible(nuevo_slug, excluir_id=tienda_id):
                return False, f"El subdominio '{nuevo_slug}' ya está en uso."
            campos["subdominio"] = nuevo_slug

        ok = self.repo.actualizar_tienda(tienda_id, campos)
        return (True, "Tienda actualizada.") if ok else (False, "Error al actualizar.")

    def cambiar_plan(self, tienda_id: str, nuevo_plan: str) -> tuple[bool, str]:
        """Cambia el plan de suscripción."""
        if nuevo_plan not in self.PLANES:
            return False, f"Plan inválido. Opciones: {', '.join(self.PLANES)}"
        ok = self.repo.cambiar_plan(tienda_id, nuevo_plan)
        return (True, f"Plan cambiado a '{nuevo_plan}'.") if ok else (False, "Error al cambiar plan.")

    # ─────────────────────────────────────────────
    # CONSULTAS
    # ─────────────────────────────────────────────
    def listar_tiendas(self) -> list[Tienda]:
        return self.repo.listar_todas()

    def listar_activas(self) -> list[Tienda]:
        return self.repo.listar_activas()

    def obtener_tienda(self, tienda_id: str) -> Optional[Tienda]:
        return self.repo.obtener_por_id(tienda_id)

    def obtener_por_subdominio(self, subdominio: str) -> Optional[Tienda]:
        return self.repo.obtener_por_subdominio(subdominio)

    def tiendas_por_propietario(self, uid: str) -> list[Tienda]:
        return self.repo.listar_por_propietario(uid)

    # ─────────────────────────────────────────────
    # HELPERS INTERNOS
    # ─────────────────────────────────────────────
    def _slugify(self, texto: str) -> str:
        """Convierte texto a slug válido para subdominio: 'Mi Tienda S.A.' → 'mi-tienda-sa'"""
        texto = texto.lower().strip()
        texto = unicodedata.normalize("NFKD", texto)
        texto = texto.encode("ascii", "ignore").decode("ascii")
        texto = re.sub(r"[^\w\s-]", "", texto)
        texto = re.sub(r"[\s_]+", "-", texto)
        texto = re.sub(r"-+", "-", texto)
        return texto.strip("-")

    def _validar_email(self, email: str) -> bool:
        pattern = r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$"
        return bool(re.match(pattern, email, re.IGNORECASE))

    def _validar_datos(
        self, nombre, subdominio, logo_url, descripcion,
        categoria, pais_origen, email_contacto,
        telefono, direccion, plan,
    ) -> tuple[bool, str]:
        if not nombre or len(nombre.strip()) < 3:
            return False, "El nombre debe tener al menos 3 caracteres."
        if not subdominio or len(subdominio.strip()) < 3:
            return False, "El subdominio debe tener al menos 3 caracteres."
        if not descripcion or len(descripcion.strip()) < 10:
            return False, "La descripción debe tener al menos 10 caracteres."
        if categoria not in self.CATEGORIAS_VALIDAS:
            return False, f"Categoría inválida."
        if pais_origen not in self.PAISES_ORIGEN:
            return False, f"País de origen inválido."
        if not self._validar_email(email_contacto):
            return False, "El email de contacto no es válido."
        if not telefono or len(telefono.strip()) < 7:
            return False, "El teléfono debe tener al menos 7 dígitos."
        if not direccion or len(direccion.strip()) < 5:
            return False, "La dirección es requerida."
        if plan not in self.PLANES:
            return False, f"Plan inválido. Opciones: {', '.join(self.PLANES)}"
        return True, "OK"