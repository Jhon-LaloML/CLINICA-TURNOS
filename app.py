"""
Sistema de Gestión de Turnos para Clínica
==========================================

Arquitectura MVC con Flask. Base de datos con herencia
(PERSONA → CLIENTE/EMPLEADO → DOCTOR/RECEPCIONISTA).

Roles: admin, recepcionista, doctor, cliente.

Ejecutar:
    python seed.py     (1ra vez: crea BD + admin)
    python app.py
"""

from flask import Flask, redirect, url_for

from models.database import inicializar_db
from models import gestor
from controllers.auth_controller import (
    login_form, login_post, logout, redirigir_segun_rol,
    login_requerido, rol_requerido, perfil, cambiar_username, cambiar_password
)
from controllers import admin_controller as admin
from controllers import recepcion_controller as recepcion
from controllers import doctor_controller as doctor
from controllers import cliente_controller as cliente


app = Flask(__name__)
app.secret_key = "clinica-san-gabriel-estructura-datos-1-ficct-2026"

inicializar_db()


def _preparar_datos_iniciales():
    """
    Si la base de datos está vacía (sin usuario admin), carga automáticamente
    el admin y los datos de demostración. Esto es necesario en plataformas de
    hosting con sistema de archivos efímero (como Render), donde la BD se
    regenera en cada reinicio.
    """
    from models import Usuario
    if Usuario.buscar_por_username("admin") is None:
        try:
            import seed
            seed.crear_clinica()
            seed.crear_admin()
        except Exception as e:
            print(f"[INIT] No se pudo crear el admin: {e}")
        try:
            import seed_demo
            seed_demo.cargar()
        except Exception as e:
            print(f"[INIT] No se pudieron cargar los datos demo: {e}")


_preparar_datos_iniciales()
gestor.recargar()


@app.route("/")
def raiz():
    return redirect(url_for("login_form"))


# ---------------- AUTENTICACIÓN ----------------
app.add_url_rule("/login", endpoint="login_form", view_func=login_form, methods=["GET"])
app.add_url_rule("/login", endpoint="login_post", view_func=login_post, methods=["POST"])
app.add_url_rule("/logout", endpoint="logout", view_func=login_requerido(logout))
app.add_url_rule("/ir-a-mi-panel", endpoint="redirigir_segun_rol",
                 view_func=login_requerido(redirigir_segun_rol))
app.add_url_rule("/perfil", endpoint="perfil", view_func=login_requerido(perfil))
app.add_url_rule("/perfil/username", endpoint="cambiar_username",
                 view_func=login_requerido(cambiar_username), methods=["POST"])
app.add_url_rule("/perfil/password", endpoint="cambiar_password",
                 view_func=login_requerido(cambiar_password), methods=["POST"])


# ---------------- ADMIN ----------------
A = "admin"
app.add_url_rule("/admin/", endpoint="admin_dashboard",
                 view_func=rol_requerido(A)(admin.dashboard))
app.add_url_rule("/admin/especialidades", endpoint="admin_especialidades",
                 view_func=rol_requerido(A)(admin.especialidades))
app.add_url_rule("/admin/especialidades/crear", endpoint="admin_especialidad_crear",
                 view_func=rol_requerido(A)(admin.especialidad_crear), methods=["POST"])
app.add_url_rule("/admin/especialidades/<int:especialidad_id>/editar",
                 endpoint="admin_especialidad_editar",
                 view_func=rol_requerido(A)(admin.especialidad_editar), methods=["POST"])
app.add_url_rule("/admin/especialidades/<int:especialidad_id>/eliminar",
                 endpoint="admin_especialidad_eliminar",
                 view_func=rol_requerido(A)(admin.especialidad_eliminar), methods=["POST"])

app.add_url_rule("/admin/consultorios", endpoint="admin_consultorios",
                 view_func=rol_requerido(A)(admin.consultorios))
app.add_url_rule("/admin/consultorios/crear", endpoint="admin_consultorio_crear",
                 view_func=rol_requerido(A)(admin.consultorio_crear), methods=["POST"])
app.add_url_rule("/admin/consultorios/<int:consultorio_id>/editar",
                 endpoint="admin_consultorio_editar",
                 view_func=rol_requerido(A)(admin.consultorio_editar), methods=["POST"])
app.add_url_rule("/admin/consultorios/<int:consultorio_id>/eliminar",
                 endpoint="admin_consultorio_eliminar",
                 view_func=rol_requerido(A)(admin.consultorio_eliminar), methods=["POST"])

app.add_url_rule("/admin/empleados", endpoint="admin_empleados",
                 view_func=rol_requerido(A)(admin.empleados))
app.add_url_rule("/admin/empleados/nuevo", endpoint="admin_empleado_nuevo_form",
                 view_func=rol_requerido(A)(admin.empleado_nuevo_form))
app.add_url_rule("/admin/empleados/crear", endpoint="admin_empleado_crear",
                 view_func=rol_requerido(A)(admin.empleado_crear), methods=["POST"])

app.add_url_rule("/admin/horarios", endpoint="admin_horarios",
                 view_func=rol_requerido(A)(admin.horarios))
app.add_url_rule("/admin/horarios/<int:doctor_id>", endpoint="admin_horarios_doctor",
                 view_func=rol_requerido(A)(admin.horarios_doctor))
app.add_url_rule("/admin/horarios/<int:doctor_id>/agregar", endpoint="admin_horario_agregar",
                 view_func=rol_requerido(A)(admin.horario_agregar), methods=["POST"])
app.add_url_rule("/admin/horarios/<int:doctor_id>/<int:horario_id>/eliminar",
                 endpoint="admin_horario_eliminar",
                 view_func=rol_requerido(A)(admin.horario_eliminar), methods=["POST"])

# Clientes (admin)
app.add_url_rule("/admin/clientes", endpoint="admin_clientes",
                 view_func=rol_requerido(A)(admin.clientes))
app.add_url_rule("/admin/clientes/<int:cliente_id>/editar", endpoint="admin_cliente_editar_form",
                 view_func=rol_requerido(A)(admin.cliente_editar_form))
app.add_url_rule("/admin/clientes/<int:cliente_id>/guardar", endpoint="admin_cliente_editar",
                 view_func=rol_requerido(A)(admin.cliente_editar), methods=["POST"])

# Editar doctor
app.add_url_rule("/admin/doctores/<int:doctor_id>/editar", endpoint="admin_doctor_editar_form",
                 view_func=rol_requerido(A)(admin.doctor_editar_form))
app.add_url_rule("/admin/doctores/<int:doctor_id>/guardar", endpoint="admin_doctor_editar",
                 view_func=rol_requerido(A)(admin.doctor_editar), methods=["POST"])

# Editar recepcionista
app.add_url_rule("/admin/recepcionistas/<int:recep_id>/editar",
                 endpoint="admin_recepcionista_editar_form",
                 view_func=rol_requerido(A)(admin.recepcionista_editar_form))
app.add_url_rule("/admin/recepcionistas/<int:recep_id>/guardar",
                 endpoint="admin_recepcionista_editar",
                 view_func=rol_requerido(A)(admin.recepcionista_editar), methods=["POST"])


# ---------------- RECEPCIÓN ----------------
R = "recepcionista"
app.add_url_rule("/recepcion/", endpoint="recepcion_dashboard",
                 view_func=rol_requerido(R)(recepcion.dashboard))
app.add_url_rule("/recepcion/buscar", endpoint="recepcion_buscar_cliente",
                 view_func=rol_requerido(R)(recepcion.buscar_cliente))
app.add_url_rule("/recepcion/cliente/nuevo", endpoint="recepcion_registrar_cliente_form",
                 view_func=rol_requerido(R)(recepcion.registrar_cliente_form))
app.add_url_rule("/recepcion/cliente/crear", endpoint="recepcion_registrar_cliente",
                 view_func=rol_requerido(R)(recepcion.registrar_cliente), methods=["POST"])
app.add_url_rule("/recepcion/ficha/nueva", endpoint="recepcion_generar_ficha_form",
                 view_func=rol_requerido(R)(recepcion.generar_ficha_form))
app.add_url_rule("/recepcion/ficha/crear", endpoint="recepcion_generar_ficha",
                 view_func=rol_requerido(R)(recepcion.generar_ficha), methods=["POST"])
app.add_url_rule("/recepcion/ficha/<int:ficha_id>/generada", endpoint="recepcion_ficha_generada",
                 view_func=rol_requerido(R)(recepcion.ficha_generada))
app.add_url_rule("/recepcion/colas", endpoint="recepcion_ver_colas",
                 view_func=rol_requerido(R)(recepcion.ver_colas))
app.add_url_rule("/recepcion/clientes", endpoint="recepcion_lista_clientes",
                 view_func=rol_requerido(R)(recepcion.lista_clientes))


# ---------------- DOCTOR ----------------
D = "doctor"
app.add_url_rule("/doctor/", endpoint="doctor_dashboard",
                 view_func=rol_requerido(D)(doctor.dashboard))
app.add_url_rule("/doctor/llamar", endpoint="doctor_llamar_siguiente",
                 view_func=rol_requerido(D)(doctor.llamar_siguiente), methods=["POST"])
app.add_url_rule("/doctor/atendido", endpoint="doctor_marcar_atendido",
                 view_func=rol_requerido(D)(doctor.marcar_atendido), methods=["POST"])
app.add_url_rule("/doctor/ausente", endpoint="doctor_marcar_ausente",
                 view_func=rol_requerido(D)(doctor.marcar_ausente), methods=["POST"])
app.add_url_rule("/doctor/cerrar", endpoint="doctor_cerrar_inscripciones",
                 view_func=rol_requerido(D)(doctor.cerrar_inscripciones), methods=["POST"])
app.add_url_rule("/doctor/reabrir", endpoint="doctor_reabrir_inscripciones",
                 view_func=rol_requerido(D)(doctor.reabrir_inscripciones), methods=["POST"])
app.add_url_rule("/doctor/historial", endpoint="doctor_historial",
                 view_func=rol_requerido(D)(doctor.historial))


# ---------------- CLIENTE ----------------
C = "cliente"
app.add_url_rule("/cliente/", endpoint="cliente_dashboard",
                 view_func=rol_requerido(C)(cliente.dashboard))
app.add_url_rule("/cliente/ficha", endpoint="cliente_mi_ficha",
                 view_func=rol_requerido(C)(cliente.mi_ficha))
app.add_url_rule("/cliente/historial", endpoint="cliente_historial",
                 view_func=rol_requerido(C)(cliente.historial))
app.add_url_rule("/api/mi-ficha", endpoint="api_mi_ficha",
                 view_func=rol_requerido(C)(cliente.api_mi_ficha))


if __name__ == "__main__":
    import os
    # En producción (Render, etc.) el puerto viene de la variable de entorno PORT.
    # En local usa 8000 por defecto.
    puerto = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=puerto, debug=True)
