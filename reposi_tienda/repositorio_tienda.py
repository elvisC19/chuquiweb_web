import uuid
from datetime import datetime
from typing import Optional

from config.firebase_config import get_firestore_client
from tienda.modelo_tienda import Tienda


class RepositorioTienda:
    """
    Capa de repositorio: acceso directo a Firebase Firestore.
    Colección: 'tiendas'
    """

    COLECCION = "tiendas"

    def __init__(self):
        self.db = get_firestore_client()

    # ─────────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────────
    def crear_tienda(self, tienda: Tienda) -> Tienda:
        """Guarda una nueva tienda en Firestore."""
        self.db.collection(self.COLECCION).document(tienda.tienda_id).set(
            tienda.to_dict()
        )
        return tienda

    # ─────────────────────────────────────────────
    # READ
    # ─────────────────────────────────────────────
    def obtener_por_id(self, tienda_id: str) -> Optional[Tienda]:
        """Devuelve una tienda por su ID o None si no existe."""
        doc = self.db.collection(self.COLECCION).document(tienda_id).get()
        if doc.exists:
            return Tienda.from_dict(doc.to_dict())
        return None

    def obtener_por_subdominio(self, subdominio: str) -> Optional[Tienda]:
        """Busca una tienda por su subdominio único."""
        docs = (
            self.db.collection(self.COLECCION)
            .where("subdominio", "==", subdominio)
            .limit(1)
            .stream()
        )
        for doc in docs:
            return Tienda.from_dict(doc.to_dict())
        return None

    def listar_todas(self) -> list[Tienda]:
        """Retorna todas las tiendas ordenadas por fecha de registro."""
        docs = (
            self.db.collection(self.COLECCION)
            .order_by("fecha_registro", direction="DESCENDING")
            .stream()
        )
        return [Tienda.from_dict(doc.to_dict()) for doc in docs]

    def listar_activas(self) -> list[Tienda]:
        """Retorna solo las tiendas con estado activo=True."""
        docs = (
            self.db.collection(self.COLECCION)
            .where("activo", "==", True)
            .stream()
        )
        return [Tienda.from_dict(doc.to_dict()) for doc in docs]

    def listar_por_propietario(self, uid_propietario: str) -> list[Tienda]:
        """Retorna las tiendas de un usuario importadora específico."""
        docs = (
            self.db.collection(self.COLECCION)
            .where("uid_propietario", "==", uid_propietario)
            .stream()
        )
        return [Tienda.from_dict(doc.to_dict()) for doc in docs]

    # ─────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────
    def actualizar_tienda(self, tienda_id: str, campos: dict) -> bool:
        """Actualiza campos específicos de una tienda."""
        try:
            self.db.collection(self.COLECCION).document(tienda_id).update(campos)
            return True
        except Exception:
            return False

    def cambiar_estado(self, tienda_id: str, activo: bool) -> bool:
        """Activa o desactiva una tienda (baja lógica)."""
        return self.actualizar_tienda(tienda_id, {"activo": activo})

    def cambiar_plan(self, tienda_id: str, plan: str) -> bool:
        """Cambia el plan de suscripción de una tienda."""
        return self.actualizar_tienda(tienda_id, {"plan": plan})

    # ─────────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────────
    def eliminar_tienda(self, tienda_id: str) -> bool:
        """Elimina físicamente una tienda de Firestore."""
        try:
            self.db.collection(self.COLECCION).document(tienda_id).delete()
            return True
        except Exception:
            return False

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────
    def subdominio_disponible(self, subdominio: str, excluir_id: str = "") -> bool:
        """Verifica si un subdominio ya está en uso."""
        docs = (
            self.db.collection(self.COLECCION)
            .where("subdominio", "==", subdominio)
            .stream()
        )
        for doc in docs:
            if doc.id != excluir_id:
                return False  # ya existe
        return True  # disponible

    def generar_id(self) -> str:
        """Genera un ID único para nueva tienda."""
        return str(uuid.uuid4())