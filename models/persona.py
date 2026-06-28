"""
Modelo Persona
==============

Tabla padre de la jerarquía de herencia:

    PERSONA
      ├── CLIENTE
      └── EMPLEADO → DOCTOR / RECEPCIONISTA

Guarda los datos comunes a todas las personas: ci, nombre, apellido,
teléfono y el discriminador 'tipo' ('cliente' o 'empleado').

Cada persona puede tener una cuenta de usuario (usuario_id) para el login.
"""

from .database import obtener_conexion


class Persona:
    """Datos comunes de cualquier persona del sistema."""

    def __init__(self, id, ci, nombre, apellido, tipo,
                 telefono=None, usuario_id=None, username=None):
        self.id = id
        self.ci = ci
        self.nombre = nombre
        self.apellido = apellido
        self.tipo = tipo
        self.telefono = telefono
        self.usuario_id = usuario_id
        self.username = username

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @staticmethod
    def crear(ci, nombre, apellido, tipo, telefono="", usuario_id=None):
        """
        Inserta una persona.
        :param tipo: 'cliente' o 'empleado'
        :raises ValueError: si el CI ya existe o faltan datos.
        """
        ci = ci.strip()
        nombre = nombre.strip()
        apellido = apellido.strip()
        if not ci or not nombre or not apellido:
            raise ValueError("CI, nombre y apellido son obligatorios.")
        if tipo not in ("cliente", "empleado"):
            raise ValueError("El tipo de persona debe ser 'cliente' o 'empleado'.")

        conexion = obtener_conexion()
        existe = conexion.execute(
            "SELECT id FROM persona WHERE ci = ?", (ci,)
        ).fetchone()
        if existe:
            conexion.close()
            raise ValueError(f"Ya existe una persona con el CI '{ci}'.")

        cursor = conexion.cursor()
        cursor.execute(
            """INSERT INTO persona (usuario_id, ci, nombre, apellido, telefono, tipo)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (usuario_id, ci, nombre, apellido, telefono.strip(), tipo)
        )
        nuevo_id = cursor.lastrowid
        conexion.commit()
        conexion.close()
        return nuevo_id

    @staticmethod
    def buscar_por_ci(ci):
        conexion = obtener_conexion()
        fila = conexion.execute("""
            SELECT p.*, u.username AS username
            FROM persona p LEFT JOIN usuario u ON p.usuario_id = u.id
            WHERE p.ci = ?
        """, (ci.strip(),)).fetchone()
        conexion.close()
        return Persona._desde_fila(fila) if fila else None

    @staticmethod
    def buscar_por_id(persona_id):
        conexion = obtener_conexion()
        fila = conexion.execute("""
            SELECT p.*, u.username AS username
            FROM persona p LEFT JOIN usuario u ON p.usuario_id = u.id
            WHERE p.id = ?
        """, (persona_id,)).fetchone()
        conexion.close()
        return Persona._desde_fila(fila) if fila else None

    @staticmethod
    def buscar_por_usuario_id(usuario_id):
        conexion = obtener_conexion()
        fila = conexion.execute("""
            SELECT p.*, u.username AS username
            FROM persona p LEFT JOIN usuario u ON p.usuario_id = u.id
            WHERE p.usuario_id = ?
        """, (usuario_id,)).fetchone()
        conexion.close()
        return Persona._desde_fila(fila) if fila else None

    @staticmethod
    def _desde_fila(fila):
        return Persona(
            id=fila["id"], ci=fila["ci"], nombre=fila["nombre"],
            apellido=fila["apellido"], tipo=fila["tipo"],
            telefono=fila["telefono"], usuario_id=fila["usuario_id"],
            username=fila["username"]
        )

    def __repr__(self):
        return f"Persona({self.nombre_completo}, CI={self.ci}, {self.tipo})"

    @staticmethod
    def editar(persona_id, nombre, apellido, telefono=""):
        """Actualiza los datos básicos de una persona."""
        nombre = nombre.strip()
        apellido = apellido.strip()
        if not nombre or not apellido:
            raise ValueError("Nombre y apellido son obligatorios.")
        conexion = obtener_conexion()
        conexion.execute(
            "UPDATE persona SET nombre=?, apellido=?, telefono=? WHERE id=?",
            (nombre, apellido, telefono.strip(), persona_id)
        )
        conexion.commit()
        conexion.close()
