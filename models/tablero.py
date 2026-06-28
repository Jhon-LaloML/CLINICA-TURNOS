"""
Módulo Tablero del Día
======================

Calcula qué doctores atienden hoy y en qué consultorio, navegando
la herencia DOCTOR → EMPLEADO → PERSONA y la tabla HORARIO_TRABAJO.
"""

from datetime import datetime
from .database import obtener_conexion

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def nombre_dia_actual():
    return DIAS[datetime.now().weekday()]


def consultorios_activos_hoy():
    """
    Lista de consultorios con doctor asignado hoy.
    Cada item: consultorio_id, consultorio_numero, consultorio_ubicacion,
    doctor_id, doctor_nombre, especialidad, hora_inicio, hora_fin.
    """
    dia_hoy = datetime.now().weekday()
    conexion = obtener_conexion()
    filas = conexion.execute("""
        SELECT
            c.id AS consultorio_id,
            c.numero AS consultorio_numero,
            c.ubicacion AS consultorio_ubicacion,
            d.id AS doctor_id,
            p.nombre || ' ' || p.apellido AS doctor_nombre,
            esp.nombre AS especialidad,
            h.hora_inicio, h.hora_fin
        FROM horario_trabajo h
        JOIN doctor d        ON h.doctor_id = d.id
        JOIN empleado e      ON d.empleado_id = e.id
        JOIN persona p       ON e.persona_id = p.id
        JOIN especialidad esp ON d.especialidad_id = esp.id
        JOIN consultorio c   ON h.consultorio_id = c.id
        WHERE h.dia_semana = ?
        ORDER BY c.numero, h.hora_inicio
    """, (dia_hoy,)).fetchall()
    conexion.close()
    return [dict(f) for f in filas]


def consultorio_del_doctor_hoy(doctor_id):
    """Consultorio donde atiende un doctor hoy (o None)."""
    dia_hoy = datetime.now().weekday()
    conexion = obtener_conexion()
    fila = conexion.execute("""
        SELECT c.id AS consultorio_id, c.numero AS consultorio_numero,
               c.ubicacion AS consultorio_ubicacion,
               h.hora_inicio, h.hora_fin,
               esp.nombre AS especialidad,
               p.nombre || ' ' || p.apellido AS doctor_nombre
        FROM horario_trabajo h
        JOIN doctor d   ON h.doctor_id = d.id
        JOIN empleado e ON d.empleado_id = e.id
        JOIN persona p  ON e.persona_id = p.id
        JOIN especialidad esp ON d.especialidad_id = esp.id
        JOIN consultorio c ON h.consultorio_id = c.id
        WHERE h.doctor_id = ? AND h.dia_semana = ?
        ORDER BY h.hora_inicio LIMIT 1
    """, (doctor_id, dia_hoy)).fetchone()
    conexion.close()
    return dict(fila) if fila else None
