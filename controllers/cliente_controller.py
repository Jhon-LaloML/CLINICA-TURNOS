"""
Controlador del Cliente
=======================

El cliente entra con su login y ve:
- Inicio: información de la clínica + su ficha activa (si tiene).
- Mi ficha: el detalle de su turno, a qué consultorio ir, y cuántos hay
  delante de él EN ESA COLA (solo la de su consultorio).
- Mi historial: sus atenciones pasadas.

El cliente NO ve las colas de otros consultorios, solo la suya.
"""

from flask import render_template, jsonify, session

from models import Cliente, Ficha, Doctor, gestor, tablero
from models.database import obtener_conexion


def _cliente_actual():
    return Cliente.buscar_por_usuario_id(session.get("usuario_id"))


def _info_clinica():
    """Devuelve los datos de la clínica (la primera registrada)."""
    conexion = obtener_conexion()
    fila = conexion.execute("SELECT * FROM clinica LIMIT 1").fetchone()
    conexion.close()
    return dict(fila) if fila else None


# ================================================================
# Inicio: info de la clínica + resumen de su ficha
# ================================================================
def dashboard():
    cliente = _cliente_actual()
    if cliente is None:
        return render_template("cliente/sin_perfil.html", username=session.get("username"))

    ficha = Ficha.ficha_activa_de_cliente(cliente.id)
    faltan = None
    consultorio_info = None
    if ficha:
        if ficha.estado == "en_espera":
            faltan = gestor.posicion_en_cola(ficha.consultorio_id, ficha.id)
        consultorio_info = _datos_consultorio_hoy(ficha.consultorio_id)

    return render_template(
        "cliente/dashboard.html",
        cliente=cliente,
        clinica=_info_clinica(),
        ficha=ficha,
        faltan=faltan,
        consultorio_info=consultorio_info,
        total_doctores=len(Doctor.listar_todos()),
        dia_actual=tablero.nombre_dia_actual()
    )


def _datos_consultorio_hoy(consultorio_id):
    """Doctor y especialidad que atienden hoy en ese consultorio."""
    for c in tablero.consultorios_activos_hoy():
        if c["consultorio_id"] == consultorio_id:
            return c
    return None


# ================================================================
# Mi ficha (con la cola de SU consultorio)
# ================================================================
def mi_ficha():
    cliente = _cliente_actual()
    if cliente is None:
        return render_template("cliente/sin_perfil.html", username=session.get("username"))

    ficha = Ficha.ficha_activa_de_cliente(cliente.id)
    if ficha is None:
        return render_template("cliente/mi_ficha.html", cliente=cliente, ficha=None)

    cid = ficha.consultorio_id
    faltan = gestor.posicion_en_cola(cid, ficha.id) if ficha.estado == "en_espera" else None
    actual = gestor.paciente_actual(cid)

    # La cola de SU consultorio (sin nombres de otros, solo códigos y posición)
    prioritaria = gestor.cola_prioritaria(cid)
    regular = gestor.cola_regular(cid)

    return render_template(
        "cliente/mi_ficha.html",
        cliente=cliente,
        ficha=ficha,
        faltan=faltan,
        actual=actual,
        consultorio_info=_datos_consultorio_hoy(cid),
        en_espera=gestor.cantidad_en_espera(cid),
        total_prioritaria=len(prioritaria),
        total_regular=len(regular),
        estado_consultorio=gestor.estado_consultorio(cid)
    )


def api_mi_ficha():
    """JSON para que la vista del cliente se actualice sola."""
    cliente = _cliente_actual()
    if cliente is None:
        return jsonify({"tiene_ficha": False})
    ficha = Ficha.ficha_activa_de_cliente(cliente.id)
    if ficha is None:
        return jsonify({"tiene_ficha": False})

    cid = ficha.consultorio_id
    faltan = gestor.posicion_en_cola(cid, ficha.id) if ficha.estado == "en_espera" else None
    actual = gestor.paciente_actual(cid)

    return jsonify({
        "tiene_ficha": True,
        "codigo": ficha.codigo,
        "estado": ficha.estado,
        "consultorio_numero": ficha.consultorio_numero,
        "faltan": faltan,
        "es_su_turno": ficha.estado == "atendiendo",
        "en_espera": gestor.cantidad_en_espera(cid),
        "llamando_codigo": actual["codigo"] if actual else None
    })


# ================================================================
# Mi historial
# ================================================================
def historial():
    cliente = _cliente_actual()
    if cliente is None:
        return render_template("cliente/sin_perfil.html", username=session.get("username"))
    registros = Ficha.historial_de_cliente(cliente.id)
    return render_template("cliente/historial.html", cliente=cliente, registros=registros)
