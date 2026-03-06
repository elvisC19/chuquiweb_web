# ============================================================
#  user/modelo_usuario.py
#  Capa de Modelo – Clase Usuario (Entidad de Dominio)
#  ChuquiWeb – Marketplace de Importadoras
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Usuario:
    """
    Representa un usuario del sistema ChuquiWeb.
    Esta clase es la entidad central del módulo de gestión de usuarios.
    """

    # ── Identificadores ──────────────────────────────────────
    uid: Optional[str] = None          # UID asignado por Firebase Auth
    nombre: str = ""                   # Nombre completo
    email: str = ""                    # Correo electrónico (único)
    password: str = ""                 # Contraseña (solo para creación, nunca se guarda en texto plano)

    # ── Rol y estado ─────────────────────────────────────────
    rol: str = "cliente"               # "admin" | "importadora" | "cliente"
    activo: bool = True                # True = habilitado, False = dado de baja

    # ── Metadatos ────────────────────────────────────────────
    fecha_registro: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_dict(self) -> dict:
        """
        Convierte el objeto a diccionario para guardarlo en Firestore.
        NOTA: La contraseña nunca se incluye en el diccionario de Firestore.
        """
        return {
            "uid":             self.uid,
            "nombre":          self.nombre,
            "email":           self.email,
            "rol":             self.rol,
            "activo":          self.activo,
            "fecha_registro":  self.fecha_registro,
        }

    @staticmethod
    def from_dict(data: dict) -> "Usuario":
        """
        Crea un objeto Usuario a partir de un diccionario de Firestore.
        """
        return Usuario(
            uid=            data.get("uid"),
            nombre=         data.get("nombre", ""),
            email=          data.get("email", ""),
            rol=            data.get("rol", "cliente"),
            activo=         data.get("activo", True),
            fecha_registro= data.get("fecha_registro", ""),
        )

    def __str__(self):
        estado = "ACTIVO" if self.activo else "BAJA"
        return f"[{self.rol.upper()}] {self.nombre} <{self.email}> – {estado}"
