"""
Modelo Usuario
==============

Cuentas de acceso al sistema (login) para todos los roles:
admin, recepcionista, doctor y cliente.

Las contraseñas se guardan hasheadas (nunca en texto plano).

Política de credenciales iniciales (definida con el equipo):
- username = primer nombre de la persona, en minúsculas
- contraseña = su CI
- Si el username ya existe, se agrega un número (juan, juan2, juan3...).
  El id de la tabla usuario es lo que diferencia a dos personas homónimas.
- Cada usuario puede cambiar su username luego.
"""

from werkzeug.security import generate_password_hash, check_password_hash

from .database import obtener_conexion


class Usuario:
    """Cuenta de acceso al sistema."""

    def __init__(self, id, username, rol, activo, password_hash=None):
        self.id = id
        self.username = username
        self.rol = rol
        self.activo = activo
        self.password_hash = password_hash

    # ----------------------------------------------------------------
    # Crear
    # ----------------------------------------------------------------
    @staticmethod
    def crear(username, password, rol):
        """
        Crea un usuario con contraseña hasheada.
        :raises ValueError: si el username ya existe.
        """
        conexion = obtener_conexion()
        existe = conexion.execute(
            "SELECT id FROM usuario WHERE username = ?", (username,)
        ).fetchone()
        if existe:
            conexion.close()
            raise ValueError(f"El nombre de usuario '{username}' ya está en uso.")

        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO usuario (username, password_hash, rol) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), rol)
        )
        nuevo_id = cursor.lastrowid
        conexion.commit()
        conexion.close()
        return nuevo_id

    @staticmethod
    def generar_username_unico(primer_nombre):
        """
        Genera un username único a partir del primer nombre (minúsculas, sin tildes).
        Si ya existe, agrega un número: juan, juan2, juan3...
        """
        base = _limpiar(primer_nombre.split()[0].lower()) if primer_nombre.strip() else "usuario"
        conexion = obtener_conexion()
        candidato = base
        contador = 1
        while conexion.execute(
            "SELECT id FROM usuario WHERE username = ?", (candidato,)
        ).fetchone():
            contador += 1
            candidato = f"{base}{contador}"
        conexion.close()
        return candidato

    # ----------------------------------------------------------------
    # Buscar
    # ----------------------------------------------------------------
    @staticmethod
    def buscar_por_username(username):
        conexion = obtener_conexion()
        fila = conexion.execute(
            "SELECT * FROM usuario WHERE username = ?", (username,)
        ).fetchone()
        conexion.close()
        return Usuario._desde_fila(fila) if fila else None

    @staticmethod
    def buscar_por_id(usuario_id):
        conexion = obtener_conexion()
        fila = conexion.execute(
            "SELECT * FROM usuario WHERE id = ?", (usuario_id,)
        ).fetchone()
        conexion.close()
        return Usuario._desde_fila(fila) if fila else None

    @staticmethod
    def _desde_fila(fila):
        return Usuario(
            id=fila["id"], username=fila["username"], rol=fila["rol"],
            activo=fila["activo"], password_hash=fila["password_hash"]
        )

    # ----------------------------------------------------------------
    # Verificar / actualizar
    # ----------------------------------------------------------------
    def verificar_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def cambiar_username(usuario_id, nuevo_username):
        """Permite a un usuario cambiar su nombre de acceso."""
        nuevo_username = nuevo_username.strip()
        if not nuevo_username:
            raise ValueError("El nombre de usuario no puede estar vacío.")
        conexion = obtener_conexion()
        existe = conexion.execute(
            "SELECT id FROM usuario WHERE username = ? AND id != ?",
            (nuevo_username, usuario_id)
        ).fetchone()
        if existe:
            conexion.close()
            raise ValueError(f"El nombre de usuario '{nuevo_username}' ya está en uso.")
        conexion.execute(
            "UPDATE usuario SET username = ? WHERE id = ?", (nuevo_username, usuario_id)
        )
        conexion.commit()
        conexion.close()

    @staticmethod
    def cambiar_password(usuario_id, nueva_password):
        conexion = obtener_conexion()
        conexion.execute(
            "UPDATE usuario SET password_hash = ? WHERE id = ?",
            (generate_password_hash(nueva_password), usuario_id)
        )
        conexion.commit()
        conexion.close()

    def __repr__(self):
        return f"Usuario({self.username}, rol={self.rol})"


def _limpiar(texto):
    """Quita tildes y caracteres no alfanuméricos para el username."""
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "u", "ñ": "n"
    }
    for o, l in reemplazos.items():
        texto = texto.replace(o, l)
    return "".join(c for c in texto if c.isalnum())
