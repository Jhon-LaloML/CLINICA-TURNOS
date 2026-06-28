"""
Modelo Doctor (consulta a través de la herencia)
================================================

DOCTOR → EMPLEADO → PERSONA, más ESPECIALIDAD.

Reúne con JOINs los datos dispersos en las tablas de la herencia
para mostrarlos cómodamente.
"""

from .database import obtener_conexion

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class Doctor:
    """Vista consolidada de un doctor (datos de las 3 tablas + especialidad)."""

    def __init__(self, id, persona_id, empleado_id, ci, nombre, apellido,
                 especialidad_id, especialidad_nombre, telefono=None,
                 email=None, usuario_id=None, username=None):
        self.id = id
        self.persona_id = persona_id
        self.empleado_id = empleado_id
        self.ci = ci
        self.nombre = nombre
        self.apellido = apellido
        self.especialidad_id = especialidad_id
        self.especialidad_nombre = especialidad_nombre
        self.telefono = telefono
        self.email = email
        self.usuario_id = usuario_id
        self.username = username

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"


    @staticmethod
    def editar(doctor_id, nombre, apellido, telefono, especialidad_id, email, direccion=""):
        """Actualiza los datos de un doctor a través de la herencia."""
        nombre = nombre.strip()
        apellido = apellido.strip()
        if not nombre or not apellido:
            raise ValueError("Nombre y apellido son obligatorios.")
        if not especialidad_id:
            raise ValueError("Debe seleccionar una especialidad.")
        conexion = obtener_conexion()
        # Obtener la cadena de IDs para el doctor
        fila = conexion.execute("""
            SELECT d.id, e.id AS empl_id, p.id AS pers_id
            FROM doctor d JOIN empleado e ON d.empleado_id=e.id JOIN persona p ON e.persona_id=p.id
            WHERE d.id=?
        """, (doctor_id,)).fetchone()
        if fila is None:
            conexion.close()
            raise ValueError("Doctor no encontrado.")
        # Actualizar las 3 tablas
        conexion.execute("UPDATE persona SET nombre=?, apellido=?, telefono=? WHERE id=?",
                        (nombre, apellido, telefono.strip(), fila["pers_id"]))
        conexion.execute("UPDATE empleado SET direccion=? WHERE id=?",
                        (direccion.strip(), fila["empl_id"]))
        conexion.execute("UPDATE doctor SET especialidad_id=?, email=? WHERE id=?",
                        (int(especialidad_id), email.strip(), doctor_id))
        conexion.commit()
        conexion.close()

    _SELECT = """
        SELECT d.id, d.especialidad_id, d.email,
               e.id AS empleado_id,
               p.id AS persona_id, p.ci, p.nombre, p.apellido, p.telefono,
               p.usuario_id,
               esp.nombre AS especialidad_nombre,
               u.username AS username
        FROM doctor d
        JOIN empleado e   ON d.empleado_id = e.id
        JOIN persona p    ON e.persona_id = p.id
        JOIN especialidad esp ON d.especialidad_id = esp.id
        LEFT JOIN usuario u ON p.usuario_id = u.id
    """

    @staticmethod
    def listar_todos():
        conexion = obtener_conexion()
        filas = conexion.execute(Doctor._SELECT + " ORDER BY p.apellido, p.nombre").fetchall()
        conexion.close()
        return [Doctor._desde_fila(f) for f in filas]

    @staticmethod
    def buscar_por_id(doctor_id):
        conexion = obtener_conexion()
        fila = conexion.execute(Doctor._SELECT + " WHERE d.id = ?", (doctor_id,)).fetchone()
        conexion.close()
        return Doctor._desde_fila(fila) if fila else None

    @staticmethod
    def buscar_por_usuario_id(usuario_id):
        conexion = obtener_conexion()
        fila = conexion.execute(Doctor._SELECT + " WHERE p.usuario_id = ?", (usuario_id,)).fetchone()
        conexion.close()
        return Doctor._desde_fila(fila) if fila else None

    @staticmethod
    def _desde_fila(f):
        return Doctor(
            id=f["id"], persona_id=f["persona_id"], empleado_id=f["empleado_id"],
            ci=f["ci"], nombre=f["nombre"], apellido=f["apellido"],
            especialidad_id=f["especialidad_id"], especialidad_nombre=f["especialidad_nombre"],
            telefono=f["telefono"], email=f["email"],
            usuario_id=f["usuario_id"], username=f["username"]
        )

    def __repr__(self):
        return f"Doctor({self.nombre_completo}, {self.especialidad_nombre})"


class HorarioTrabajo:
    """Bloque horario de un doctor en un consultorio."""

    def __init__(self, id, doctor_id, consultorio_id, dia_semana,
                 hora_inicio, hora_fin, consultorio_numero=None, doctor_nombre=None):
        self.id = id
        self.doctor_id = doctor_id
        self.consultorio_id = consultorio_id
        self.dia_semana = dia_semana
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.consultorio_numero = consultorio_numero
        self.doctor_nombre = doctor_nombre

    @property
    def dia_nombre(self):
        return DIAS_SEMANA[self.dia_semana]

    @staticmethod
    def agregar(doctor_id, consultorio_id, dia_semana, hora_inicio, hora_fin):
        if hora_fin <= hora_inicio:
            raise ValueError("La hora de fin debe ser posterior a la de inicio.")
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """INSERT INTO horario_trabajo
               (doctor_id, consultorio_id, dia_semana, hora_inicio, hora_fin)
               VALUES (?, ?, ?, ?, ?)""",
            (doctor_id, consultorio_id, dia_semana, hora_inicio, hora_fin)
        )
        nuevo_id = cursor.lastrowid
        conexion.commit()
        conexion.close()
        return nuevo_id

    @staticmethod
    def listar_por_doctor(doctor_id):
        conexion = obtener_conexion()
        filas = conexion.execute("""
            SELECT h.*, c.numero AS consultorio_numero
            FROM horario_trabajo h
            JOIN consultorio c ON h.consultorio_id = c.id
            WHERE h.doctor_id = ?
            ORDER BY h.dia_semana, h.hora_inicio
        """, (doctor_id,)).fetchall()
        conexion.close()
        return [HorarioTrabajo(
            id=f["id"], doctor_id=f["doctor_id"], consultorio_id=f["consultorio_id"],
            dia_semana=f["dia_semana"], hora_inicio=f["hora_inicio"],
            hora_fin=f["hora_fin"], consultorio_numero=f["consultorio_numero"]
        ) for f in filas]

    @staticmethod
    def eliminar(horario_id):
        conexion = obtener_conexion()
        conexion.execute("DELETE FROM horario_trabajo WHERE id = ?", (horario_id,))
        conexion.commit()
        conexion.close()

