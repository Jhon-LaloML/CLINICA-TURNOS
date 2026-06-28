"""
Modelo de Registro (orquestador de la herencia)
===============================================

Centraliza la creación de personas con su jerarquía completa, porque
crear un doctor implica varios pasos coordinados:

    1. crear USUARIO (login)
    2. crear PERSONA (datos comunes, tipo='empleado')
    3. crear EMPLEADO (persona_id, tipo='doctor')
    4. crear DOCTOR (empleado_id, especialidad_id)

Así los controladores llaman a una sola función y no tienen que
conocer el detalle de la herencia.

Credenciales iniciales: username = primer nombre, password = CI.
"""

from .database import obtener_conexion
from .usuario import Usuario
from .persona import Persona


def registrar_cliente(ci, nombre, apellido, telefono="", crear_cuenta=True):
    """
    Registra un cliente completo: usuario + persona + cliente.

    :return: dict con persona_id, cliente_id, username, password
    :raises ValueError: si el CI ya existe.
    """
    ci = ci.strip()
    nombre = nombre.strip()
    apellido = apellido.strip()

    if Persona.buscar_por_ci(ci):
        raise ValueError(f"Ya existe una persona registrada con el CI '{ci}'.")

    usuario_id = None
    username = None
    password = ci
    if crear_cuenta:
        username = Usuario.generar_username_unico(nombre)
        usuario_id = Usuario.crear(username, ci, rol="cliente")

    persona_id = Persona.crear(ci, nombre, apellido, "cliente", telefono, usuario_id)

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO cliente (persona_id) VALUES (?)", (persona_id,))
    cliente_id = cursor.lastrowid
    conexion.commit()
    conexion.close()

    return {
        "persona_id": persona_id, "cliente_id": cliente_id,
        "username": username, "password": password
    }


def registrar_empleado(ci, nombre, apellido, tipo_empleado, telefono="",
                        direccion="", especialidad_id=None, email="",
                        turno="", area=""):
    """
    Registra un empleado completo según su tipo.

    Para 'doctor': usuario + persona + empleado + doctor (requiere especialidad_id).
    Para 'recepcionista': usuario + persona + empleado + recepcionista.

    :return: dict con ids, username y password.
    :raises ValueError: si faltan datos o el CI ya existe.
    """
    ci = ci.strip()
    nombre = nombre.strip()
    apellido = apellido.strip()

    if tipo_empleado not in ("doctor", "recepcionista"):
        raise ValueError("El tipo de empleado debe ser 'doctor' o 'recepcionista'.")
    if tipo_empleado == "doctor" and not especialidad_id:
        raise ValueError("Debe seleccionar una especialidad para el doctor.")
    if Persona.buscar_por_ci(ci):
        raise ValueError(f"Ya existe una persona registrada con el CI '{ci}'.")

    # 1. Usuario (rol según tipo)
    username = Usuario.generar_username_unico(nombre)
    usuario_id = Usuario.crear(username, ci, rol=tipo_empleado)
    password = ci

    # 2. Persona (tipo empleado)
    persona_id = Persona.crear(ci, nombre, apellido, "empleado", telefono, usuario_id)

    # 3. Empleado
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    codigo_emp = f"EMP{persona_id:04d}"
    cursor.execute(
        """INSERT INTO empleado (persona_id, codigo_empleado, direccion, estado, tipo)
           VALUES (?, ?, ?, 'activo', ?)""",
        (persona_id, codigo_emp, direccion.strip(), tipo_empleado)
    )
    empleado_id = cursor.lastrowid

    # 4. Doctor o Recepcionista
    if tipo_empleado == "doctor":
        cursor.execute(
            "INSERT INTO doctor (empleado_id, especialidad_id, email) VALUES (?, ?, ?)",
            (empleado_id, especialidad_id, email.strip())
        )
        especifico_id = cursor.lastrowid
    else:
        cursor.execute(
            "INSERT INTO recepcionista (empleado_id, turno, area) VALUES (?, ?, ?)",
            (empleado_id, turno.strip(), area.strip())
        )
        especifico_id = cursor.lastrowid

    conexion.commit()
    conexion.close()

    return {
        "persona_id": persona_id, "empleado_id": empleado_id,
        "especifico_id": especifico_id, "username": username, "password": password
    }
