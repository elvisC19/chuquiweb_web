from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tienda:
    """
    Modelo de datos para una Tienda/Importadora en ChuquiWeb.
    Representa la entidad principal del marketplace.
    """
    tienda_id: str
    nombre: str
    subdominio: str          # ej: "importadora-lider" → lider.chuquiweb.bo
    logo_url: str
    descripcion: str
    categoria: str           # ej: "Electrónica", "Ropa", "Alimentos"
    pais_origen: str         # ej: "China", "Brasil", "EE.UU."
    email_contacto: str
    telefono: str
    direccion: str
    plan: str                # "basico" | "premium"
    activo: bool
    uid_propietario: str     # referencia al Usuario con rol "importadora"
    fecha_registro: str
    banner_url: Optional[str] = field(default=None)
    sitio_web: Optional[str] = field(default=None)
    descripcion_larga: Optional[str] = field(default=None)

    def to_dict(self) -> dict:
        """Serializa la tienda para guardar en Firestore."""
        return {
            "tienda_id": self.tienda_id,
            "nombre": self.nombre,
            "subdominio": self.subdominio,
            "logo_url": self.logo_url,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "pais_origen": self.pais_origen,
            "email_contacto": self.email_contacto,
            "telefono": self.telefono,
            "direccion": self.direccion,
            "plan": self.plan,
            "activo": self.activo,
            "uid_propietario": self.uid_propietario,
            "fecha_registro": self.fecha_registro,
            "banner_url": self.banner_url,
            "sitio_web": self.sitio_web,
            "descripcion_larga": self.descripcion_larga,
        }

    @staticmethod
    def from_dict(data: dict) -> "Tienda":
        """Deserializa un documento Firestore a objeto Tienda."""
        return Tienda(
            tienda_id=data.get("tienda_id", ""),
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
            activo=data.get("activo", True),
            uid_propietario=data.get("uid_propietario", ""),
            fecha_registro=data.get("fecha_registro", ""),
            banner_url=data.get("banner_url"),
            sitio_web=data.get("sitio_web"),
            descripcion_larga=data.get("descripcion_larga"),
        )