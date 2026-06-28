"""
Controlador del Administrador
=============================

El admin gestiona:
- Especialidades (CRUD)
- Consultorios (CRUD)
- Empleados: registrar doctores (con especialidad) y recepcionistas
- Horarios de trabajo de los doctores

Al registrar un empleado se crea su cuenta de acceso automáticamente
(usuario = primer nombre, contraseña = CI).
"""

from flask import render_template, request, redirect, url_for, flash, session

from models import (
    Especialidad, Consultorio, Doctor, Recepcionista, HorarioTrabajo,
    DIAS_SEMANA, registro, Cliente, editar_recepcionista
)


# ================================================================
# Dashboard
# ================================================================
def dashboard():
    return render_template(
        "admin/dashboard.html",
        total_especialidades=len(Especialidad.listar_todas()),
        total_consultorios=len(Consultorio.listar_todos()),
        total_doctores=len(Doctor.listar_todos()),
        total_recepcionistas=len(Recepcionista.listar_todos())
    )


# ================================================================
# Especialidades
# ================================================================
def especialidades():
    return render_template("admin/especialidades.html",
                           especialidades=Especialidad.listar_todas())


def especialidad_crear():
    try:
        Especialidad.crear(request.form.get("nombre", ""), request.form.get("descripcion", ""))
        flash("Especialidad creada correctamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_especialidades"))


def especialidad_editar(especialidad_id):
    try:
        Especialidad.editar(especialidad_id, request.form.get("nombre", ""),
                            request.form.get("descripcion", ""))
        flash("Especialidad actualizada.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_especialidades"))


def especialidad_eliminar(especialidad_id):
    try:
        Especialidad.eliminar(especialidad_id)
        flash("Especialidad eliminada.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_especialidades"))


# ================================================================
# Consultorios
# ================================================================
def consultorios():
    return render_template("admin/consultorios.html",
                           consultorios=Consultorio.listar_todos())


def consultorio_crear():
    try:
        Consultorio.crear(request.form.get("numero", ""), request.form.get("ubicacion", ""))
        flash("Consultorio creado correctamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_consultorios"))


def consultorio_editar(consultorio_id):
    try:
        Consultorio.editar(consultorio_id, request.form.get("numero", ""),
                          request.form.get("ubicacion", ""))
        flash("Consultorio actualizado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_consultorios"))


def consultorio_eliminar(consultorio_id):
    try:
        Consultorio.eliminar(consultorio_id)
        flash("Consultorio eliminado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_consultorios"))


# ================================================================
# Empleados (doctores y recepcionistas)
# ================================================================
def empleados():
    return render_template(
        "admin/empleados.html",
        doctores=Doctor.listar_todos(),
        recepcionistas=Recepcionista.listar_todos()
    )


def empleado_nuevo_form():
    return render_template(
        "admin/empleado_form.html",
        especialidades=Especialidad.listar_todas()
    )


def empleado_crear():
    """Registra un doctor o recepcionista según el tipo elegido."""
    tipo = request.form.get("tipo_empleado", "")
    ci = request.form.get("ci", "").strip()
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    telefono = request.form.get("telefono", "").strip()
    direccion = request.form.get("direccion", "").strip()

    try:
        if tipo == "doctor":
            especialidad_id = request.form.get("especialidad_id", "")
            if not especialidad_id:
                raise ValueError("Debe seleccionar una especialidad para el doctor.")
            email = request.form.get("email", "").strip()
            resultado = registro.registrar_empleado(
                ci=ci, nombre=nombre, apellido=apellido, tipo_empleado="doctor",
                telefono=telefono, direccion=direccion,
                especialidad_id=int(especialidad_id), email=email
            )
        elif tipo == "recepcionista":
            turno = request.form.get("turno", "").strip()
            area = request.form.get("area", "").strip()
            resultado = registro.registrar_empleado(
                ci=ci, nombre=nombre, apellido=apellido, tipo_empleado="recepcionista",
                telefono=telefono, direccion=direccion, turno=turno, area=area
            )
        else:
            raise ValueError("Debe indicar si es doctor o recepcionista.")

        flash(
            f"Empleado registrado correctamente. Credenciales de acceso → "
            f"usuario: {resultado['username']} / contraseña: {resultado['password']} (su CI).",
            "success"
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("admin_empleado_nuevo_form"))
    return redirect(url_for("admin_empleados"))


# ================================================================
# Horarios de trabajo
# ================================================================
def horarios():
    """Lista doctores para elegir a quién asignarle horario."""
    return render_template("admin/horarios.html", doctores=Doctor.listar_todos())


def horarios_doctor(doctor_id):
    """Muestra y gestiona los horarios de un doctor."""
    doctor = Doctor.buscar_por_id(doctor_id)
    if doctor is None:
        flash("Doctor no encontrado.", "danger")
        return redirect(url_for("admin_horarios"))
    return render_template(
        "admin/horarios_doctor.html",
        doctor=doctor,
        consultorios=Consultorio.listar_todos(),
        horarios=HorarioTrabajo.listar_por_doctor(doctor_id),
        dias_semana=DIAS_SEMANA
    )


def horario_agregar(doctor_id):
    consultorio_id = request.form.get("consultorio_id", "")
    dia_semana = request.form.get("dia_semana", "")
    hora_inicio = request.form.get("hora_inicio", "").strip()
    hora_fin = request.form.get("hora_fin", "").strip()
    try:
        if not consultorio_id or dia_semana == "" or not hora_inicio or not hora_fin:
            raise ValueError("Complete todos los campos del horario.")
        HorarioTrabajo.agregar(doctor_id, int(consultorio_id), int(dia_semana),
                               hora_inicio, hora_fin)
        flash("Horario agregado.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_horarios_doctor", doctor_id=doctor_id))


def horario_eliminar(doctor_id, horario_id):
    HorarioTrabajo.eliminar(horario_id)
    flash("Horario eliminado.", "success")
    return redirect(url_for("admin_horarios_doctor", doctor_id=doctor_id))


# ================================================================
# Clientes (admin ve y edita)
# ================================================================
def clientes():
    """Lista todos los clientes registrados."""
    return render_template("admin/clientes.html", clientes=Cliente.listar_todos())


def cliente_editar_form(cliente_id):
    cliente = Cliente.buscar_por_id(cliente_id)
    if cliente is None:
        flash("Cliente no encontrado.", "danger")
        return redirect(url_for("admin_clientes"))
    return render_template("admin/cliente_editar.html", cliente=cliente)


def cliente_editar(cliente_id):
    try:
        Cliente.editar(
            cliente_id,
            nombre=request.form.get("nombre", ""),
            apellido=request.form.get("apellido", ""),
            telefono=request.form.get("telefono", "")
        )
        flash("Datos del cliente actualizados.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_clientes"))


# ================================================================
# Editar doctor
# ================================================================
def doctor_editar_form(doctor_id):
    doctor = Doctor.buscar_por_id(doctor_id)
    if doctor is None:
        flash("Doctor no encontrado.", "danger")
        return redirect(url_for("admin_empleados"))
    return render_template("admin/doctor_editar.html",
                           doctor=doctor, especialidades=Especialidad.listar_todas())


def doctor_editar(doctor_id):
    try:
        Doctor.editar(
            doctor_id,
            nombre=request.form.get("nombre", ""),
            apellido=request.form.get("apellido", ""),
            telefono=request.form.get("telefono", ""),
            especialidad_id=request.form.get("especialidad_id", ""),
            email=request.form.get("email", ""),
            direccion=request.form.get("direccion", "")
        )
        flash("Datos del doctor actualizados.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_empleados"))


# ================================================================
# Editar recepcionista
# ================================================================
def recepcionista_editar_form(recep_id):
    recep = Recepcionista.buscar_por_id(recep_id) if hasattr(Recepcionista, 'buscar_por_id') else None
    # buscar manualmente si no hay buscar_por_id
    if recep is None:
        todos = Recepcionista.listar_todos()
        for r in todos:
            if r.id == recep_id:
                recep = r
                break
    if recep is None:
        flash("Recepcionista no encontrada.", "danger")
        return redirect(url_for("admin_empleados"))
    return render_template("admin/recepcionista_editar.html", recep=recep)


def recepcionista_editar(recep_id):
    try:
        editar_recepcionista(
            recep_id,
            nombre=request.form.get("nombre", ""),
            apellido=request.form.get("apellido", ""),
            telefono=request.form.get("telefono", ""),
            turno=request.form.get("turno", ""),
            area=request.form.get("area", "")
        )
        flash("Datos de la recepcionista actualizados.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("admin_empleados"))
