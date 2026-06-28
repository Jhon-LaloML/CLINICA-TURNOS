"""
Controlador de Autenticación
============================

Login y logout para todos los roles (admin, recepcionista, doctor, cliente),
y los decoradores que protegen las rutas según el rol.

Credenciales iniciales: usuario = primer nombre, contraseña = CI.
"""

from functools import wraps
from flask import render_template, request, redirect, url_for, flash, session

from models import Usuario


# ================================================================
# Login / Logout
# ================================================================
def login_form():
    """Muestra el formulario de login."""
    if session.get("usuario_id"):
        return redirect(url_for("redirigir_segun_rol"))
    return render_template("auth/login.html")


def login_post():
    """Procesa el login."""
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    usuario = Usuario.buscar_por_username(username)
    if usuario is None or not usuario.verificar_password(password):
        flash("Usuario o contraseña incorrectos.", "danger")
        return redirect(url_for("login_form"))

    if not usuario.activo:
        flash("Su cuenta está desactivada. Contacte al administrador.", "danger")
        return redirect(url_for("login_form"))

    # Guardar la sesión
    session["usuario_id"] = usuario.id
    session["username"] = usuario.username
    session["rol"] = usuario.rol
    flash(f"Bienvenido, {usuario.username}.", "success")
    return redirect(url_for("redirigir_segun_rol"))


def logout():
    """Cierra la sesión."""
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login_form"))


def redirigir_segun_rol():
    """Envía a cada usuario a su panel según su rol."""
    rol = session.get("rol")
    if rol == "admin":
        return redirect(url_for("admin_dashboard"))
    if rol == "recepcionista":
        return redirect(url_for("recepcion_dashboard"))
    if rol == "doctor":
        return redirect(url_for("doctor_dashboard"))
    if rol == "cliente":
        return redirect(url_for("cliente_dashboard"))
    return redirect(url_for("login_form"))


# ================================================================
# Decoradores de protección
# ================================================================
def login_requerido(vista):
    """Exige tener sesión iniciada."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not session.get("usuario_id"):
            flash("Debe iniciar sesión para continuar.", "warning")
            return redirect(url_for("login_form"))
        return vista(*args, **kwargs)
    return envoltura


def rol_requerido(*roles):
    """Exige que el usuario tenga uno de los roles indicados."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not session.get("usuario_id"):
                flash("Debe iniciar sesión para continuar.", "warning")
                return redirect(url_for("login_form"))
            if session.get("rol") not in roles:
                flash("No tiene permiso para acceder a esa sección.", "danger")
                return redirect(url_for("redirigir_segun_rol"))
            return vista(*args, **kwargs)
        return envoltura
    return decorador


# ================================================================
# Cambiar credenciales propias (cualquier usuario logueado)
# ================================================================
def perfil():
    """Página para cambiar el usuario y la contraseña propios."""
    return render_template("auth/perfil.html")


def cambiar_username():
    nuevo = request.form.get("nuevo_username", "").strip()
    try:
        Usuario.cambiar_username(session["usuario_id"], nuevo)
        session["username"] = nuevo
        flash("Nombre de usuario actualizado correctamente.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("perfil"))


def cambiar_password():
    actual = request.form.get("password_actual", "")
    nueva = request.form.get("password_nueva", "")
    confirmar = request.form.get("password_confirmar", "")

    usuario = Usuario.buscar_por_id(session["usuario_id"])
    if not usuario.verificar_password(actual):
        flash("La contraseña actual no es correcta.", "danger")
        return redirect(url_for("perfil"))
    if len(nueva) < 4:
        flash("La nueva contraseña debe tener al menos 4 caracteres.", "danger")
        return redirect(url_for("perfil"))
    if nueva != confirmar:
        flash("La confirmación no coincide con la nueva contraseña.", "danger")
        return redirect(url_for("perfil"))

    Usuario.cambiar_password(session["usuario_id"], nueva)
    flash("Contraseña actualizada correctamente.", "success")
    return redirect(url_for("perfil"))
