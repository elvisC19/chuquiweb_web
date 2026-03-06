# ============================================================
#  servi_user/servicio_usuario.py
#  Capa de Servicio – Lógica de Negocio
#  ChuquiWeb – Marketplace de Importadoras
# ============================================================
#
#  RESPONSABILIDAD: Contiene las REGLAS DE NEGOCIO del módulo
#  de usuarios. Valida datos, orquesta llamadas al repositorio
#  y retorna resultados limpios a la capa de vista.
#  No sabe nada de CustomTkinter ni de Firebase directamente.
# ============================================================

import re
import requests
from typing import Optional, List, Tuple

from user.modelo_usuario import Usuario
from reposi_user.repositorio_usuario import RepositorioUsuario
from config.firebase_config import FIREBASE_API_KEY, FIREBASE_AUTH_URL


class ServicioUsuario:
    """
    Lógica de negocio para la gestión de usuarios.
    """

    def __init__(self, repositorio: RepositorioUsuario):
        self.repo = repositorio

    # ── VALIDACIONES ─────────────────────────────────────────

    def _validar_email(self, email: str) -> bool:
        patron = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$"
        return bool(re.match(patron, email))

    def _validar_password(self, password: str) -> Tuple[bool, str]:
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres."
        return True, ""

    def _validar_datos_usuario(self, nombre: str, email: str, password: str) -> Tuple[bool, str]:
        if not nombre.strip():
            return False, "El nombre no puede estar vacío."
        if not self._validar_email(email):
            return False, "El formato del correo electrónico no es válido."
        valido, msg = self._validar_password(password)
        if not valido:
            return False, msg
        return True, ""

    # ── ALTA DE USUARIO ──────────────────────────────────────

    def alta_usuario(
        self,
        nombre: str,
        email: str,
        password: str,
        rol: str = "cliente"
    ) -> Tuple[bool, str]:
        """
        Crea un nuevo usuario en Firebase Auth y Firestore.

        Returns:
            (True, "Mensaje de éxito") o (False, "Mensaje de error")
        """
        # 1. Validar datos
        valido, msg = self._validar_datos_usuario(nombre, email, password)
        if not valido:
            return False, msg

        # 2. Construir objeto usuario
        nuevo_usuario = Usuario(
            nombre=nombre.strip(),
            email=email.strip().lower(),
            password=password,
            rol=rol,
            activo=True,
        )

        # 3. Crear en Firebase Auth
        try:
            uid = self.repo.crear_en_auth(nuevo_usuario)
            nuevo_usuario.uid = uid
        except Exception as e:
            if "EMAIL_EXISTS" in str(e) or "email-already-exists" in str(e):
                return False, "Ya existe un usuario con ese correo electrónico."
            return False, f"Error al crear cuenta: {str(e)}"

        # 4. Guardar perfil en Firestore
        try:
            self.repo.guardar_en_firestore(nuevo_usuario)
        except Exception as e:
            return False, f"Usuario creado en Auth pero error en Firestore: {str(e)}"

        return True, f"Usuario '{nombre}' creado exitosamente."

    # ── BAJA DE USUARIO ──────────────────────────────────────

    def baja_usuario(self, uid: str, permanente: bool = False) -> Tuple[bool, str]:
        """
        Da de baja a un usuario.

        Args:
            uid: UID del usuario en Firebase.
            permanente: Si True, elimina completamente. Si False, solo desactiva.

        Returns:
            (True, "Mensaje de éxito") o (False, "Mensaje de error")
        """
        if not uid:
            return False, "UID de usuario inválido."

        try:
            if permanente:
                # Eliminación completa
                self.repo.eliminar_de_firestore(uid)
                self.repo.eliminar_de_auth(uid)
                return True, "Usuario eliminado permanentemente del sistema."
            else:
                # Solo desactivar (baja lógica)
                self.repo.actualizar_estado(uid, activo=False)
                return True, "Usuario dado de baja correctamente."
        except Exception as e:
            return False, f"Error al dar de baja: {str(e)}"

    # ── LOGIN ─────────────────────────────────────────────────

    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[Usuario]]:
        """
        Autentica un usuario con email y contraseña usando la REST API de Firebase.

        Returns:
            (True, "OK", usuario) o (False, "mensaje de error", None)
        """
        if not self._validar_email(email):
            return False, "Formato de correo inválido.", None

        try:
            # Firebase Auth REST API – Sign In With Email/Password
            url = f"{FIREBASE_AUTH_URL}:signInWithPassword?key={FIREBASE_API_KEY}"
            payload = {
                "email": email.strip().lower(),
                "password": password,
                "returnSecureToken": True,
            }
            response = requests.post(url, json=payload)
            data = response.json()

            if "error" in data:
                codigo = data["error"].get("message", "")
                if "EMAIL_NOT_FOUND" in codigo or "INVALID_LOGIN_CREDENTIALS" in codigo:
                    return False, "Correo o contraseña incorrectos.", None
                if "USER_DISABLED" in codigo:
                    return False, "Esta cuenta ha sido desactivada.", None
                return False, f"Error de autenticación: {codigo}", None

            # Login exitoso – obtener perfil desde Firestore
            uid = data.get("localId")
            usuario = self.repo.obtener_por_uid(uid)

            if not usuario:
                return False, "Cuenta autenticada pero perfil no encontrado.", None
            if not usuario.activo:
                return False, "Esta cuenta está dada de baja.", None

            return True, "Login exitoso.", usuario

        except Exception as e:
            return False, f"Error de conexión: {str(e)}", None

    # ── LISTADO ───────────────────────────────────────────────

    def listar_usuarios(self, solo_activos: bool = False) -> List[Usuario]:
        """
        Retorna la lista de usuarios.

        Args:
            solo_activos: Si True, solo devuelve usuarios activos.
        """
        try:
            if solo_activos:
                return self.repo.obtener_activos()
            return self.repo.obtener_todos()
        except Exception:
            return []

    def obtener_usuario(self, uid: str) -> Optional[Usuario]:
        """Retorna un usuario por su UID."""
        try:
            return self.repo.obtener_por_uid(uid)
        except Exception:
            return None
