"""
servi_user/servicio_usuario.py
Capa de servicio: lógica de negocio para gestión de usuarios.
"""

import re
from datetime import datetime
from typing import Optional

import requests
import os

from user.modelo_usuario import Usuario
from reposi_user.repositorio_usuario import RepositorioUsuario


class ServicioUsuario:

    ROLES_VALIDOS = ["admin", "importadora", "cliente"]
    ROLES_CON_ACCESO_ADMIN = ["admin"]   # ← solo admin entra al panel

    def __init__(self):
        self.repo = RepositorioUsuario()
        self._api_key = os.environ.get("FIREBASE_API_KEY", "")

    # ─────────────────────────────────────────────
    # CONTROL DE ACCESO
    # ─────────────────────────────────────────────
    def tiene_acceso_admin(self, rol: str) -> bool:
        """Retorna True solo si el rol permite entrar al panel de administración."""
        return rol in self.ROLES_CON_ACCESO_ADMIN

    # ─────────────────────────────────────────────
    # AUTENTICACIÓN — Email / Password
    # ─────────────────────────────────────────────
    def login(self, email: str, password: str) -> tuple[bool, str, Optional[Usuario]]:
        """
        Autentica con Firebase REST API (email + password).
        Retorna (éxito, mensaje, usuario).
        """
        if not email or not password:
            return False, "Email y contraseña son obligatorios.", None

        url = (
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
            f"?key={self._api_key}"
        )
        payload = {"email": email, "password": password, "returnSecureToken": True}

        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
        except Exception as e:
            return False, f"Error de conexión con Firebase: {str(e)}", None

        if "error" in data:
            msg_firebase = data["error"].get("message", "Error desconocido")
            msg = self._traducir_error_firebase(msg_firebase)
            return False, msg, None

        uid = data.get("localId")
        usuario = self.repo.obtener_por_uid(uid)
        if not usuario:
            return False, "Usuario no encontrado en la base de datos.", None

        if not usuario.activo:
            return False, "Esta cuenta está desactivada. Contacta al administrador.", None

        return True, "Login exitoso.", usuario

    # ─────────────────────────────────────────────
    # AUTENTICACIÓN — Google (ID Token)
    # ─────────────────────────────────────────────
    def login_con_google(self, id_token: str) -> tuple[bool, str, Optional[Usuario]]:
        """
        Verifica el ID Token de Google con Firebase REST API.
        Si el usuario no existe en Firestore, lo crea automáticamente con rol 'cliente'.
        Retorna (éxito, mensaje, usuario).
        """
        if not id_token:
            return False, "Token de Google inválido.", None

        # Verificar token con Firebase
        url = (
            f"https://identitytoolkit.googleapis.com/v1/accounts:lookup"
            f"?key={self._api_key}"
        )
        try:
            resp = requests.post(url, json={"idToken": id_token}, timeout=10)
            data = resp.json()
        except Exception as e:
            return False, f"Error de conexión: {str(e)}", None

        if "error" in data:
            return False, "Token de Google inválido o expirado.", None

        usuarios_firebase = data.get("users", [])
        if not usuarios_firebase:
            return False, "No se encontró el usuario en Firebase.", None

        fb_user = usuarios_firebase[0]
        uid     = fb_user.get("localId")
        email   = fb_user.get("email", "")
        nombre  = fb_user.get("displayName", email.split("@")[0] if email else "Usuario")

        # Buscar en Firestore
        usuario = self.repo.obtener_por_uid(uid)

        if not usuario:
            # Primer login con Google → crear con rol 'cliente'
            from uuid import uuid4
            usuario = Usuario(
                uid=uid,
                nombre=nombre,
                email=email,
                password="",          # Google maneja la auth
                rol="cliente",
                activo=True,
                fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            self.repo.guardar_usuario(usuario)

        if not usuario.activo:
            return False, "Esta cuenta está desactivada.", None

        return True, "Login con Google exitoso.", usuario

    # ─────────────────────────────────────────────
    # ALTA DE USUARIO
    # ─────────────────────────────────────────────
    def crear_usuario(
        self,
        nombre: str,
        email: str,
        password: str,
        rol: str,
    ) -> tuple[bool, str, Optional[Usuario]]:
        """Crea un usuario en Firebase Auth + Firestore."""

        ok, msg = self._validar_datos_creacion(nombre, email, password, rol)
        if not ok:
            return False, msg, None

        # Verificar email único
        if self.repo.obtener_por_email(email):
            return False, f"El email '{email}' ya está registrado.", None

        # Crear en Firebase Auth
        uid, err = self._crear_en_firebase_auth(email, password)
        if err:
            return False, err, None

        usuario = Usuario(
            uid=uid,
            nombre=nombre.strip(),
            email=email.strip().lower(),
            password="",          # no se almacena en Firestore
            rol=rol,
            activo=True,
            fecha_registro=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        try:
            self.repo.guardar_usuario(usuario)
            return True, "Usuario creado correctamente.", usuario
        except Exception as e:
            return False, f"Error al guardar en Firestore: {str(e)}", None

    # ─────────────────────────────────────────────
    # EDICIÓN DE USUARIO  ← CORRECCIÓN PRINCIPAL
    # ─────────────────────────────────────────────
    def editar_usuario(
        self,
        uid: str,
        nombre: str = None,
        email: str = None,
        password: str = None,
        rol: str = None,
        activo: bool = None,
    ) -> tuple[bool, str]:
        """
        Edita los campos indicados de un usuario existente.
        Solo actualiza los campos que se pasen (no None).
        Email y password se actualizan también en Firebase Auth.
        """
        usuario = self.repo.obtener_por_uid(uid)
        if not usuario:
            return False, "Usuario no encontrado."

        campos_firestore = {}
        campos_firebase_auth = {}

        # ── Nombre ──────────────────────────────
        if nombre is not None:
            nombre = nombre.strip()
            if len(nombre) < 2:
                return False, "El nombre debe tener al menos 2 caracteres."
            campos_firestore["nombre"] = nombre

        # ── Email ────────────────────────────────
        if email is not None:
            email = email.strip().lower()
            if not self._validar_email(email):
                return False, "El email no tiene un formato válido."
            if email != usuario.email:
                existente = self.repo.obtener_por_email(email)
                if existente and existente.uid != uid:
                    return False, f"El email '{email}' ya está en uso por otro usuario."
                campos_firestore["email"] = email
                campos_firebase_auth["email"] = email

        # ── Contraseña ───────────────────────────
        if password is not None and password.strip():
            password = password.strip()
            if len(password) < 6:
                return False, "La contraseña debe tener al menos 6 caracteres."
            campos_firebase_auth["password"] = password

        # ── Rol ──────────────────────────────────
        if rol is not None:
            if rol not in self.ROLES_VALIDOS:
                return False, f"Rol inválido. Opciones: {', '.join(self.ROLES_VALIDOS)}"
            campos_firestore["rol"] = rol

        # ── Estado activo ────────────────────────
        if activo is not None:
            campos_firestore["activo"] = activo

        if not campos_firestore and not campos_firebase_auth:
            return False, "No se indicaron campos a actualizar."

        # ── Actualizar Firebase Auth (email / password) ──
        if campos_firebase_auth:
            err = self._actualizar_firebase_auth(uid, campos_firebase_auth)
            if err:
                return False, f"Error al actualizar Firebase Auth: {err}"

        # ── Actualizar Firestore ──
        if campos_firestore:
            ok = self.repo.actualizar_usuario(uid, campos_firestore)
            if not ok:
                return False, "Error al actualizar Firestore."

        return True, "Usuario actualizado correctamente."

    # ─────────────────────────────────────────────
    # BAJA LÓGICA
    # ─────────────────────────────────────────────
    def desactivar_usuario(self, uid: str) -> tuple[bool, str]:
        usuario = self.repo.obtener_por_uid(uid)
        if not usuario:
            return False, "Usuario no encontrado."
        if not usuario.activo:
            return False, "El usuario ya está desactivado."
        ok = self.repo.actualizar_usuario(uid, {"activo": False})
        return (True, "Usuario desactivado.") if ok else (False, "Error al desactivar.")

    def activar_usuario(self, uid: str) -> tuple[bool, str]:
        usuario = self.repo.obtener_por_uid(uid)
        if not usuario:
            return False, "Usuario no encontrado."
        if usuario.activo:
            return False, "El usuario ya está activo."
        ok = self.repo.actualizar_usuario(uid, {"activo": True})
        return (True, "Usuario activado.") if ok else (False, "Error al activar.")

    # ─────────────────────────────────────────────
    # CONSULTAS
    # ─────────────────────────────────────────────
    def listar_usuarios(self) -> list[Usuario]:
        return self.repo.listar_todos()

    def obtener_usuario(self, uid: str) -> Optional[Usuario]:
        return self.repo.obtener_por_uid(uid)

    # ─────────────────────────────────────────────
    # HELPERS PRIVADOS
    # ─────────────────────────────────────────────
    def _crear_en_firebase_auth(self, email: str, password: str) -> tuple[Optional[str], Optional[str]]:
        """Crea el usuario en Firebase Auth y retorna (uid, error)."""
        url = (
            f"https://identitytoolkit.googleapis.com/v1/accounts:signUp"
            f"?key={self._api_key}"
        )
        try:
            resp = requests.post(
                url,
                json={"email": email, "password": password, "returnSecureToken": True},
                timeout=10,
            )
            data = resp.json()
        except Exception as e:
            return None, str(e)

        if "error" in data:
            return None, self._traducir_error_firebase(data["error"].get("message", ""))
        return data.get("localId"), None

    def _actualizar_firebase_auth(self, uid: str, campos: dict) -> Optional[str]:
        """
        Actualiza email y/o password en Firebase Auth usando Admin REST API.
        Requiere el campo 'localId' para identificar al usuario.
        Retorna None si OK, o string con el error.
        """
        url = (
            f"https://identitytoolkit.googleapis.com/v1/accounts:update"
            f"?key={self._api_key}"
        )
        payload = {"localId": uid, **campos}
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
        except Exception as e:
            return str(e)

        if "error" in data:
            return self._traducir_error_firebase(data["error"].get("message", ""))
        return None

    def _validar_email(self, email: str) -> bool:
        return bool(re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-z]{2,}$", email, re.I))

    def _validar_datos_creacion(self, nombre, email, password, rol) -> tuple[bool, str]:
        if not nombre or len(nombre.strip()) < 2:
            return False, "El nombre debe tener al menos 2 caracteres."
        if not email or not self._validar_email(email):
            return False, "El email no es válido."
        if not password or len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres."
        if rol not in self.ROLES_VALIDOS:
            return False, f"Rol inválido. Opciones: {', '.join(self.ROLES_VALIDOS)}"
        return True, "OK"

    def _traducir_error_firebase(self, msg: str) -> str:
        errores = {
            "EMAIL_NOT_FOUND":       "No existe una cuenta con ese email.",
            "INVALID_PASSWORD":      "Contraseña incorrecta.",
            "USER_DISABLED":         "Esta cuenta está deshabilitada.",
            "EMAIL_EXISTS":          "El email ya está registrado.",
            "WEAK_PASSWORD":         "La contraseña debe tener al menos 6 caracteres.",
            "INVALID_EMAIL":         "El formato del email no es válido.",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Demasiados intentos. Intenta más tarde.",
            "INVALID_LOGIN_CREDENTIALS": "Email o contraseña incorrectos.",
        }
        for key, traduccion in errores.items():
            if key in msg:
                return traduccion
        return f"Error de autenticación: {msg}"