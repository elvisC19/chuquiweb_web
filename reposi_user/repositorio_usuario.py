"""
reposi_user/repositorio_usuario.py
Capa de repositorio: acceso directo a Firebase Firestore para usuarios.
"""

from typing import Optional
from config.firebase_config import get_firestore_client
from user.modelo_usuario import Usuario


class RepositorioUsuario:

    COLECCION = "usuarios"

    def __init__(self):
        self.db = get_firestore_client()

    # ─────────────────────────────────────────────
    # CREATE / UPSERT
    # ─────────────────────────────────────────────
    def guardar_usuario(self, usuario: Usuario) -> None:
        """Guarda o reemplaza un usuario en Firestore (upsert por uid)."""
        self.db.collection(self.COLECCION).document(usuario.uid).set(
            usuario.to_dict()
        )

    # ─────────────────────────────────────────────
    # READ
    # ─────────────────────────────────────────────
    def obtener_por_uid(self, uid: str) -> Optional[Usuario]:
        doc = self.db.collection(self.COLECCION).document(uid).get()
        if doc.exists:
            return Usuario.from_dict(doc.to_dict())
        return None

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Busca un usuario por email (útil para validar unicidad)."""
        docs = (
            self.db.collection(self.COLECCION)
            .where("email", "==", email.lower())
            .limit(1)
            .stream()
        )
        for doc in docs:
            return Usuario.from_dict(doc.to_dict())
        return None

    def listar_todos(self) -> list[Usuario]:
        docs = (
            self.db.collection(self.COLECCION)
            .order_by("fecha_registro", direction="DESCENDING")
            .stream()
        )
        return [Usuario.from_dict(doc.to_dict()) for doc in docs]

    # ─────────────────────────────────────────────
    # UPDATE  ← NUEVO
    # ─────────────────────────────────────────────
    def actualizar_usuario(self, uid: str, campos: dict) -> bool:
        """
        Actualiza solo los campos indicados de un usuario existente.
        Retorna True si tuvo éxito.
        """
        try:
            self.db.collection(self.COLECCION).document(uid).update(campos)
            return True
        except Exception:
            return False