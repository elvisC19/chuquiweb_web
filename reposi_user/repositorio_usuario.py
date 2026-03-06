# ============================================================
#  reposi_user/repositorio_usuario.py
#  Capa de Repositorio – Acceso directo a Firebase
#  ChuquiWeb – Marketplace de Importadoras
# ============================================================
#
#  RESPONSABILIDAD: Esta capa es la ÚNICA que habla con Firebase.
#  No contiene lógica de negocio. Solo operaciones CRUD sobre
#  Firestore y Firebase Authentication.
# ============================================================

from firebase_admin import auth, firestore
from user.modelo_usuario import Usuario
from typing import Optional, List


COLECCION_USUARIOS = "usuarios"   # Nombre de la colección en Firestore


class RepositorioUsuario:
    """
    Acceso a datos de usuarios en Firebase (Firestore + Auth).
    """

    def __init__(self, db):
        """
        Args:
            db: Cliente de Firestore obtenido desde firebase_config.
        """
        self.db = db
        self.coleccion = db.collection(COLECCION_USUARIOS)

    # ── CREATE ──────────────────────────────────────────────

    def crear_en_auth(self, usuario: Usuario) -> str:
        """
        Crea el usuario en Firebase Authentication.
        Retorna el UID generado por Firebase.
        """
        user_record = auth.create_user(
            email=usuario.email,
            password=usuario.password,
            display_name=usuario.nombre,
            disabled=not usuario.activo,
        )
        return user_record.uid

    def guardar_en_firestore(self, usuario: Usuario) -> None:
        """
        Guarda o actualiza el perfil del usuario en Firestore.
        El documento se identifica por el UID de Firebase Auth.
        """
        self.coleccion.document(usuario.uid).set(usuario.to_dict())

    # ── READ ─────────────────────────────────────────────────

    def obtener_por_uid(self, uid: str) -> Optional[Usuario]:
        """
        Busca un usuario en Firestore por su UID.
        Retorna None si no existe.
        """
        doc = self.coleccion.document(uid).get()
        if doc.exists:
            return Usuario.from_dict(doc.to_dict())
        return None

    def obtener_todos(self) -> List[Usuario]:
        """
        Retorna todos los usuarios registrados en Firestore.
        """
        docs = self.coleccion.stream()
        return [Usuario.from_dict(doc.to_dict()) for doc in docs]

    def obtener_activos(self) -> List[Usuario]:
        """
        Retorna solo los usuarios con estado activo=True.
        """
        docs = self.coleccion.where("activo", "==", True).stream()
        return [Usuario.from_dict(doc.to_dict()) for doc in docs]

    # ── UPDATE ───────────────────────────────────────────────

    def actualizar_estado(self, uid: str, activo: bool) -> None:
        """
        Actualiza el campo 'activo' en Firestore.
        También deshabilita/habilita la cuenta en Firebase Auth.
        """
        self.coleccion.document(uid).update({"activo": activo})
        auth.update_user(uid, disabled=not activo)

    # ── DELETE ───────────────────────────────────────────────

    def eliminar_de_auth(self, uid: str) -> None:
        """
        Elimina permanentemente el usuario de Firebase Authentication.
        """
        auth.delete_user(uid)

    def eliminar_de_firestore(self, uid: str) -> None:
        """
        Elimina el documento del usuario en Firestore.
        """
        self.coleccion.document(uid).delete()

    # ── AUTH (Login) ─────────────────────────────────────────

    def verificar_token(self, id_token: str) -> Optional[dict]:
        """
        Verifica un token JWT de Firebase Authentication.
        Retorna el payload decodificado o None si es inválido.
        """
        try:
            decoded = auth.verify_id_token(id_token)
            return decoded
        except Exception:
            return None
