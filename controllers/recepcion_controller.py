"""
Controlador de Recepción
========================

La recepcionista:
- Ve el tablero del día (consultorios activos y sus colas).
- Busca clientes por CI; si no existe, lo registra.
- Genera fichas (encola al cliente en un consultorio, con prioridad).

La recepción NO mueve la cola: solo genera fichas. El avance lo hace el doctor.
"""

from flask import render_template, request, redirect, url_for, flash, session

from models import (
    Cliente, Ficha, Consultorio, Recepcionista, gestor, tablero, registro
)


def _recepcionista_actual():
    """Devuelve el id de recepcionista del usuario logueado (o None)."""
    rec = Recepcionista.buscar_por_usuario_id(session.get("usuario_id"))
    return rec.id if rec else None


# ================================================================
# Dashboard / Tablero del día
# ================================================================
def dashboard():
    activos = tablero.consultorios_activos_hoy()
    datos = []
    for c in activos:
        cid = c["consultorio_id"]
        datos.append({
            **c,
            "en_espera": gestor.cantidad_en_espera(cid),
            "en_prioritaria": len(gestor.cola_prioritaria(cid)),
            "en_regular": len(gestor.cola_regular(cid)),
            "proximo": gestor.proximo_de(cid),
        })
    return render_template(
        "recepcion/dashboard.html",
        dia_actual=tablero.nombre_dia_actual(),
        tablero=datos
    )


# ================================================================
# Buscar / registrar cliente
# ================================================================
def buscar_cliente():
    ci = request.args.get("ci", "").strip()
    cliente = None
    buscado = False
    if ci:
        buscado = True
        cliente = Cliente.buscar_por_ci(ci)
    return render_template("recepcion/buscar_cliente.html",
                           ci=ci, cliente=cliente, buscado=buscado)


def registrar_cliente_form():
    ci = request.args.get("ci", "").strip()
    return render_template("recepcion/registrar_cliente.html", ci=ci)


def registrar_cliente():
    ci = request.form.get("ci", "").strip()
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    telefono = request.form.get("telefono", "").strip()
    try:
        resultado = registro.registrar_cliente(ci, nombre, apellido, telefono, crear_cuenta=True)
        flash(
            f"Cliente registrado. Puede entrar al sistema con → "
            f"usuario: {resultado['username']} / contraseña: {resultado['password']} (su CI).",
            "success"
        )
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("recepcion_registrar_cliente_form", ci=ci))
    return redirect(url_for("recepcion_generar_ficha_form", ci=ci))


# ================================================================
# Generar ficha
# ================================================================
def generar_ficha_form():
    ci = request.args.get("ci", "").strip()
    cliente = Cliente.buscar_por_ci(ci) if ci else None
    if cliente is None:
        flash("Primero busque o registre al cliente.", "warning")
        return redirect(url_for("recepcion_buscar_cliente"))

    activos = tablero.consultorios_activos_hoy()
    for c in activos:
        c["en_espera"] = gestor.cantidad_en_espera(c["consultorio_id"])
    por_especialidad = {}
    for c in activos:
        por_especialidad.setdefault(c["especialidad"], []).append(c)

    # Verificar si el cliente ya tiene una ficha activa hoy
    ficha_activa = Ficha.ficha_activa_de_cliente(cliente.id)

    return render_template(
        "recepcion/generar_ficha.html",
        cliente=cliente,
        consultorios_activos=activos,
        por_especialidad=por_especialidad,
        ficha_activa=ficha_activa
    )


def generar_ficha():
    cliente_id = request.form.get("cliente_id", "")
    consultorio_id = request.form.get("consultorio_id", "")
    tipo = request.form.get("tipo", "regular")
    motivo = request.form.get("motivo", "").strip()

    cliente = Cliente.buscar_por_id(int(cliente_id)) if cliente_id else None
    consultorio = Consultorio.buscar_por_id(int(consultorio_id)) if consultorio_id else None

    if cliente is None or consultorio is None:
        flash("Datos incompletos para generar la ficha.", "danger")
        return redirect(url_for("recepcion_buscar_cliente"))

    # No permitir más de una ficha activa simultánea
    if Ficha.ficha_activa_de_cliente(cliente.id):
        flash("El cliente ya tiene una ficha activa hoy. Debe ser atendido o marcado ausente antes de generar otra.", "warning")
        return redirect(url_for("recepcion_generar_ficha_form", ci=cliente.ci))

    # Verificar que el consultorio acepte nuevos
    if not gestor.puede_recibir(consultorio.id):
        flash(f"El Consultorio {consultorio.numero} ya no acepta más pacientes hoy.", "warning")
        return redirect(url_for("recepcion_generar_ficha_form", ci=cliente.ci))

    try:
        ficha = Ficha.crear(
            cliente_id=cliente.id, consultorio_id=consultorio.id,
            consultorio_numero=consultorio.numero, tipo=tipo, motivo=motivo,
            recepcionista_id=_recepcionista_actual()
        )
        gestor.encolar_ficha(ficha)
        flash(f"Ficha {ficha.codigo} generada para {cliente.nombre_completo}.", "success")
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("recepcion_generar_ficha_form", ci=cliente.ci))
    return redirect(url_for("recepcion_ficha_generada", ficha_id=ficha.id))


def ficha_generada(ficha_id):
    ficha = Ficha.buscar_por_id(ficha_id)
    if ficha is None:
        flash("Ficha no encontrada.", "danger")
        return redirect(url_for("recepcion_dashboard"))
    faltan = gestor.posicion_en_cola(ficha.consultorio_id, ficha.id)
    return render_template("recepcion/ficha_generada.html", ficha=ficha, faltan=faltan)


# ================================================================
# Ver colas
# ================================================================
def ver_colas():
    activos = tablero.consultorios_activos_hoy()
    datos = []
    for c in activos:
        cid = c["consultorio_id"]
        datos.append({
            **c,
            "prioritaria": gestor.cola_prioritaria(cid),
            "regular": gestor.cola_regular(cid),
        })
    return render_template("recepcion/ver_colas.html",
                           dia_actual=tablero.nombre_dia_actual(), colas=datos)


# ================================================================
# Lista de clientes (solo visualización para recepción)
# ================================================================
def lista_clientes():
    """La recepcionista puede ver todos los clientes registrados."""
    q = request.args.get("q", "").strip()
    todos = Cliente.listar_todos()
    if q:
        q_lower = q.lower()
        todos = [c for c in todos if q_lower in c.nombre.lower()
                 or q_lower in c.apellido.lower()
                 or q_lower in (c.ci or "")]
    return render_template("recepcion/lista_clientes.html", clientes=todos, q=q)
