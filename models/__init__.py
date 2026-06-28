"""
Modelos del Sistema de Gestión de Turnos para Clínica (estructura con herencia).
"""

from .database import inicializar_db, obtener_conexion
from .usuario import Usuario
from .persona import Persona
from .especialidad import Especialidad
from .consultorio import Consultorio
from .doctor import Doctor, HorarioTrabajo, DIAS_SEMANA
from .cliente import Cliente, Recepcionista, editar_recepcionista
from .cola import Cola
from .pila import Pila
from .ficha import Ficha
from .gestor_turnos import GestorTurnos, gestor
from . import tablero
from . import registro

__all__ = [
    "inicializar_db", "obtener_conexion", "Usuario", "Persona",
    "Especialidad", "Consultorio", "Doctor", "HorarioTrabajo", "DIAS_SEMANA",
    "Cliente", "Recepcionista", "Cola", "Pila", "Ficha",
    "GestorTurnos", "gestor", "tablero", "registro"
]
