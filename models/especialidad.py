"""
Modelo Especialidad
===================
CRUD de especialidades médicas.
"""

from .database import obtener_conexion


class Especialidad:
    def __init__(self, id, nombre, descripcion=None):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion

    @staticmethod
    def crear(nombre, descripcion=""):
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre de la especialidad es obligatorio.")
        conexion = obtener_conexion()
        if conexion.execute("SELECT id FROM especialidad WHERE nombre = ?", (nombre,)).fetchone():
            conexion.close()
            raise ValueError(f"La especialidad '{nombre}' ya existe.")
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO especialidad (nombre, descripcion) VALUES (?, ?)",
                       (nombre, descripcion.strip()))
        nuevo_id = cursor.lastrowid
        conexion.commit()
        conexion.close()
        return nuevo_id

    @staticmethod
    def listar_todas():
        conexion = obtener_conexion()
        filas = conexion.execute("SELECT * FROM especialidad ORDER BY nombre").fetchall()
        conexion.close()
        return [Especialidad(f["id"], f["nombre"], f["descripcion"]) for f in filas]

    @staticmethod
    def buscar_por_id(esp_id):
        conexion = obtener_conexion()
        fila = conexion.execute("SELECT * FROM especialidad WHERE id = ?", (esp_id,)).fetchone()
        conexion.close()
        return Especialidad(fila["id"], fila["nombre"], fila["descripcion"]) if fila else None

    @staticmethod
    def editar(esp_id, nombre, descripcion=""):
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre es obligatorio.")
        conexion = obtener_conexion()
        if conexion.execute("SELECT id FROM especialidad WHERE nombre = ? AND id != ?",
                            (nombre, esp_id)).fetchone():
            conexion.close()
            raise ValueError(f"Ya existe otra especialidad '{nombre}'.")
        conexion.execute("UPDATE especialidad SET nombre = ?, descripcion = ? WHERE id = ?",
                        (nombre, descripcion.strip(), esp_id))
        conexion.commit()
        conexion.close()

    @staticmethod
    def eliminar(esp_id):
        conexion = obtener_conexion()
        n = conexion.execute("SELECT COUNT(*) AS n FROM doctor WHERE especialidad_id = ?",
                            (esp_id,)).fetchone()["n"]
        if n > 0:
            conexion.close()
            raise ValueError("No se puede eliminar: hay doctores con esta especialidad.")
        conexion.execute("DELETE FROM especialidad WHERE id = ?", (esp_id,))
        conexion.commit()
        conexion.close()

    def __repr__(self):
        return f"Especialidad({self.nombre})"
