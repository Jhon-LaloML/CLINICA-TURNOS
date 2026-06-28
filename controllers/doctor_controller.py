"""
Controlador del Doctor
======================

El doctor es quien MUEVE la cola:
- Ver su cola (del consultorio que le toca hoy).
- Llamar al siguiente (desencola, prioritaria primero).
- Marcar atendido (apila en historial) — puede anotar diagnóstico.
- Marcar ausente.
- Cerrar / reabrir inscripciones.
- Ver su historial del día.
"""

from flask import render_template, request, redirect, url_for, flash, session

from models import Doctor, Ficha, gestor, tablero
from models.gestor_turnos import (
    ESTADO_ATENDIENDO, ESTADO_NO_RECIBE, ESTADO_FINALIZADO
)


def _doctor_y_consultorio():
    doctor = Doctor.buscar_por_usuario_id(session.get("usuario_id"))
    if doctor is None:
        return None, None
    return doctor, tablero.consultorio_del_doctor_hoy(doctor.id)


def dashboard():
    doctor, consultorio = _doctor_y_consultorio()
    if doctor is None:
        flash("No se encontró su perfil de doctor.", "danger")
        return render_template("doctor/sin_consultorio.html", motivo="perfil")
    if consultorio is None:
        return render_template("doctor/sin_consultorio.html",
                               doctor=doctor, dia_actual=tablero.nombre_dia_actual(),
                               motivo="sin_horario")
    cid = consultorio["consultorio_id"]
    return render_template(
        "doctor/mi_cola.html",
        doctor=doctor, consultorio=consultorio,
        actual=gestor.paciente_actual(cid),
        prioritaria=gestor.cola_prioritaria(cid),
        regular=gestor.cola_regular(cid),
        proximo=gestor.proximo_de(cid),
        en_espera=gestor.cantidad_en_espera(cid),
        atendidos_hoy=gestor.cantidad_atendidos(cid),
        estado=gestor.estado_consultorio(cid),
        ESTADO_ATENDIENDO=ESTADO_ATENDIENDO,
        ESTADO_NO_RECIBE=ESTADO_NO_RECIBE,
        ESTADO_FINALIZADO=ESTADO_FINALIZADO
    )


def llamar_siguiente():
    doctor, consultorio = _doctor_y_consultorio()
    if consultorio is None:
        return redirect(url_for("doctor_dashboard"))
    cid = consultorio["consultorio_id"]
    if gestor.paciente_actual(cid) is not None:
        flash("Ya tiene un paciente en atención. Ciérrelo antes de llamar al siguiente.", "warning")
        return redirect(url_for("doctor_dashboard"))
    paciente = gestor.llamar_siguiente(cid)
    if paciente is None:
        flash("No hay pacientes en espera.", "info")
    else:
        Ficha.actualizar_estado(paciente["ficha_id"], "atendiendo")
        flash(f"Llamando a {paciente['codigo']} — {paciente['cliente_nombre']}.", "success")
    return redirect(url_for("doctor_dashboard"))


def marcar_atendido():
    doctor, consultorio = _doctor_y_consultorio()
    if consultorio is None:
        return redirect(url_for("doctor_dashboard"))
    cid = consultorio["consultorio_id"]
    diagnostico = request.form.get("diagnostico", "").strip()

    actual = gestor.paciente_actual(cid)
    paciente = gestor.marcar_atendido(cid)
    if paciente is None:
        flash("No hay paciente en atención.", "info")
    else:
        Ficha.actualizar_estado(paciente["ficha_id"], "atendido", registrar_atencion=True)
        if diagnostico:
            Ficha.guardar_diagnostico(paciente["ficha_id"], diagnostico)
        flash(f"Paciente {paciente['codigo']} atendido.", "success")
    return redirect(url_for("doctor_dashboard"))


def marcar_ausente():
    doctor, consultorio = _doctor_y_consultorio()
    if consultorio is None:
        return redirect(url_for("doctor_dashboard"))
    cid = consultorio["consultorio_id"]
    paciente = gestor.marcar_ausente(cid)
    if paciente is None:
        flash("No hay paciente en atención.", "info")
    else:
        Ficha.actualizar_estado(paciente["ficha_id"], "ausente", registrar_atencion=True)
        flash(f"Paciente {paciente['codigo']} marcado como ausente.", "warning")
    return redirect(url_for("doctor_dashboard"))


def cerrar_inscripciones():
    doctor, consultorio = _doctor_y_consultorio()
    if consultorio is None:
        return redirect(url_for("doctor_dashboard"))
    gestor.cerrar_inscripciones(consultorio["consultorio_id"])
    flash("Inscripciones cerradas. Seguirá atendiendo a los que ya esperan.", "info")
    return redirect(url_for("doctor_dashboard"))


def reabrir_inscripciones():
    doctor, consultorio = _doctor_y_consultorio()
    if consultorio is None:
        return redirect(url_for("doctor_dashboard"))
    gestor.reabrir_inscripciones(consultorio["consultorio_id"])
    flash("Inscripciones reabiertas.", "success")
    return redirect(url_for("doctor_dashboard"))


def historial():
    doctor, consultorio = _doctor_y_consultorio()
    if doctor is None:
        return redirect(url_for("doctor_dashboard"))
    if consultorio is None:
        return render_template("doctor/sin_consultorio.html",
                               doctor=doctor, dia_actual=tablero.nombre_dia_actual(),
                               motivo="sin_horario")
    cid = consultorio["consultorio_id"]
    registros = gestor.historial_de(cid)
    atendidos = sum(1 for r in registros if r.get("estado_final") == "atendido")
    ausentes = sum(1 for r in registros if r.get("estado_final") == "ausente")
    return render_template(
        "doctor/historial.html",
        doctor=doctor, consultorio=consultorio, registros=registros,
        total=len(registros), atendidos=atendidos, ausentes=ausentes
    )
