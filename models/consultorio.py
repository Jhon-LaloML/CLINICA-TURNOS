"""
Modelo Consultorio
==================
CRUD de consultorios. Pertenecen a una clínica.
"""

from .database import obtener_conexion


class Consultorio:
    def __init__(self, id, numero, ubicacion=None, clinica_id=None):
        self.id = id
        self.numero = numero
        self.ubicacion = ubicacion
        self.clinica_id = clinica_id

    @staticmethod
    def crear(numero, ubicacion="", clinica_id=None):
        numero = str(numero).strip()
        if not numero:
            raise ValueError("El número del consultorio es obligatorio.")
        conexion = obtener_conexion()
        if conexion.execute("SELECT id FROM consultorio WHERE numero = ?", (numero,)).fetchone():
            conexion.close()
            raise ValueError(f"El consultorio '{numero}' ya existe.")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO consultorio (numero, ubicacion, clinica_id) VALUES (?, ?, ?)",
                       (numero, ubicacion.strip(), clinica_id))
        nuevo_id = cursor.lastrowid
        conexion.commit()
        conexion.close()
        return nuevo_id

    @staticmethod
    def listar_todos():
        conexion = obtener_conexion()
        filas = conexion.execute("SELECT * FROM consultorio ORDER BY numero").fetchall()
        conexion.close()
        return [Consultorio(f["id"], f["numero"], f["ubicacion"], f["clinica_id"]) for f in filas]

    @staticmethod
    def buscar_por_id(cons_id):
        conexion = obtener_conexion()
        fila = conexion.execute("SELECT * FROM consultorio WHERE id = ?", (cons_id,)).fetchone()
        conexion.close()
        return Consultorio(fila["id"], fila["numero"], fila["ubicacion"], fila["clinica_id"]) if fila else None

    @staticmethod
    def editar(cons_id, numero, ubicacion=""):
        numero = str(numero).strip()
        if not numero:
            raise ValueError("El número es obligatorio.")
        conexion = obtener_conexion()
        if conexion.execute("SELECT id FROM consultorio WHERE numero = ? AND id != ?",
                            (numero, cons_id)).fetchone():
            conexion.close()
            raise ValueError(f"Ya existe otro consultorio '{numero}'.")
        conexion.execute("UPDATE consultorio SET numero = ?, ubicacion = ? WHERE id = ?",
                        (numero, ubicacion.strip(), cons_id))
        conexion.commit()
        conexion.close()

    @staticmethod
    def eliminar(cons_id):
        conexion = obtener_conexion()
        n = conexion.execute("SELECT COUNT(*) AS n FROM horario_trabajo WHERE consultorio_id = ?",
                            (cons_id,)).fetchone()["n"]
        if n > 0:
            conexion.close()
            raise ValueError("No se puede eliminar: hay horarios en este consultorio.")
        conexion.execute("DELETE FROM consultorio WHERE id = ?", (cons_id,))
        conexion.commit()
        conexion.close()

    def __repr__(self):
        return f"Consultorio({self.numero})"
