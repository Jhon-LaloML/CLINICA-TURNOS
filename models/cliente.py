"""
Modelo Cliente y Recepcionista (consulta a través de la herencia)
"""

from .database import obtener_conexion


class Cliente:
    def __init__(self, id, persona_id, ci, nombre, apellido,
                 telefono=None, usuario_id=None, username=None):
        self.id = id
        self.persona_id = persona_id
        self.ci = ci
        self.nombre = nombre
        self.apellido = apellido
        self.telefono = telefono
        self.usuario_id = usuario_id
        self.username = username

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    _SELECT = """
        SELECT cl.id, cl.persona_id,
               p.ci, p.nombre, p.apellido, p.telefono, p.usuario_id,
               u.username AS username
        FROM cliente cl
        JOIN persona p ON cl.persona_id = p.id
        LEFT JOIN usuario u ON p.usuario_id = u.id
    """

    @staticmethod
    def listar_todos():
        conexion = obtener_conexion()
        filas = conexion.execute(Cliente._SELECT + " ORDER BY p.apellido, p.nombre").fetchall()
        conexion.close()
        return [Cliente._desde_fila(f) for f in filas]

    @staticmethod
    def buscar_por_ci(ci):
        conexion = obtener_conexion()
        fila = conexion.execute(Cliente._SELECT + " WHERE p.ci = ?", (ci.strip(),)).fetchone()
        conexion.close()
        return Cliente._desde_fila(fila) if fila else None

    @staticmethod
    def buscar_por_id(cliente_id):
        conexion = obtener_conexion()
        fila = conexion.execute(Cliente._SELECT + " WHERE cl.id = ?", (cliente_id,)).fetchone()
        conexion.close()
        return Cliente._desde_fila(fila) if fila else None

    @staticmethod
    def buscar_por_usuario_id(usuario_id):
        conexion = obtener_conexion()
        fila = conexion.execute(Cliente._SELECT + " WHERE p.usuario_id = ?", (usuario_id,)).fetchone()
        conexion.close()
        return Cliente._desde_fila(fila) if fila else None

    @staticmethod
    def editar(cliente_id, nombre, apellido, telefono=""):
        """Actualiza los datos básicos de un cliente."""
        nombre = nombre.strip()
        apellido = apellido.strip()
        if not nombre or not apellido:
            raise ValueError("Nombre y apellido son obligatorios.")
        conexion = obtener_conexion()
        fila = conexion.execute(
            "SELECT persona_id FROM cliente WHERE id=?", (cliente_id,)
        ).fetchone()
        if fila is None:
            conexion.close()
            raise ValueError("Cliente no encontrado.")
        conexion.execute(
            "UPDATE persona SET nombre=?, apellido=?, telefono=? WHERE id=?",
            (nombre, apellido, telefono.strip(), fila["persona_id"])
        )
        conexion.commit()
        conexion.close()

    @staticmethod
    def _desde_fila(f):
        return Cliente(
            id=f["id"], persona_id=f["persona_id"], ci=f["ci"],
            nombre=f["nombre"], apellido=f["apellido"], telefono=f["telefono"],
            usuario_id=f["usuario_id"], username=f["username"]
        )

    def __repr__(self):
        return f"Cliente({self.nombre_completo}, CI={self.ci})"


class Recepcionista:
    def __init__(self, id, persona_id, empleado_id, ci, nombre, apellido,
                 turno=None, area=None, usuario_id=None, username=None):
        self.id = id
        self.persona_id = persona_id
        self.empleado_id = empleado_id
        self.ci = ci
        self.nombre = nombre
        self.apellido = apellido
        self.turno = turno
        self.area = area
        self.usuario_id = usuario_id
        self.username = username

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    _SELECT = """
        SELECT r.id, r.turno, r.area,
               e.id AS empleado_id,
               p.id AS persona_id, p.ci, p.nombre, p.apellido, p.usuario_id,
               u.username AS username
        FROM recepcionista r
        JOIN empleado e ON r.empleado_id = e.id
        JOIN persona p  ON e.persona_id = p.id
        LEFT JOIN usuario u ON p.usuario_id = u.id
    """

    @staticmethod
    def listar_todos():
        conexion = obtener_conexion()
        filas = conexion.execute(Recepcionista._SELECT + " ORDER BY p.apellido").fetchall()
        conexion.close()
        return [Recepcionista._desde_fila(f) for f in filas]

    @staticmethod
    def buscar_por_id(recep_id):
        conexion = obtener_conexion()
        fila = conexion.execute(Recepcionista._SELECT + " WHERE r.id = ?", (recep_id,)).fetchone()
        conexion.close()
        return Recepcionista._desde_fila(fila) if fila else None

    @staticmethod
    def buscar_por_usuario_id(usuario_id):
        conexion = obtener_conexion()
        fila = conexion.execute(
            Recepcionista._SELECT + " WHERE p.usuario_id = ?", (usuario_id,)
        ).fetchone()
        conexion.close()
        return Recepcionista._desde_fila(fila) if fila else None

    @staticmethod
    def _desde_fila(f):
        return Recepcionista(
            id=f["id"], persona_id=f["persona_id"], empleado_id=f["empleado_id"],
            ci=f["ci"], nombre=f["nombre"], apellido=f["apellido"],
            turno=f["turno"], area=f["area"],
            usuario_id=f["usuario_id"], username=f["username"]
        )

    def __repr__(self):
        return f"Recepcionista({self.nombre_completo})"


def editar_recepcionista(recep_id, nombre, apellido, telefono="", turno="", area=""):
    """Actualiza los datos de una recepcionista a través de la herencia."""
    nombre = nombre.strip()
    apellido = apellido.strip()
    if not nombre or not apellido:
        raise ValueError("Nombre y apellido son obligatorios.")
    conexion = obtener_conexion()
    fila = conexion.execute("""
        SELECT r.id, e.id AS empl_id, p.id AS pers_id
        FROM recepcionista r
        JOIN empleado e ON r.empleado_id = e.id
        JOIN persona p  ON e.persona_id = p.id
        WHERE r.id = ?
    """, (recep_id,)).fetchone()
    if fila is None:
        conexion.close()
        raise ValueError("Recepcionista no encontrada.")
    conexion.execute(
        "UPDATE persona SET nombre=?, apellido=?, telefono=? WHERE id=?",
        (nombre, apellido, telefono.strip(), fila["pers_id"])
    )
    conexion.execute(
        "UPDATE recepcionista SET turno=?, area=? WHERE id=?",
        (turno.strip(), area.strip(), recep_id)
    )
    conexion.commit()
    conexion.close()
