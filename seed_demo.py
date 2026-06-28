"""
Carga datos de demostración: especialidades, consultorios, doctores
(que atienden todos los días para poder probar cualquier día) y una recepcionista.
Ejecutar después de seed.py: python seed_demo.py
"""
from models import inicializar_db, Especialidad, Consultorio, Doctor, HorarioTrabajo, registro


def cargar():
    inicializar_db()

    print("[DEMO] Especialidades...")
    esp = {}
    for nombre, desc in [("Cardiología", "Corazón"), ("Pediatría", "Niños"), ("Odontología", "Dental")]:
        try:
            esp[nombre] = Especialidad.crear(nombre, desc)
        except ValueError:
            for e in Especialidad.listar_todas():
                if e.nombre == nombre:
                    esp[nombre] = e.id

    print("[DEMO] Consultorios...")
    cons = {}
    for num, ubic in [("1", "Planta baja - norte"), ("2", "Planta baja - sur"), ("3", "Primer piso")]:
        try:
            cons[num] = Consultorio.crear(num, ubic)
        except ValueError:
            for c in Consultorio.listar_todos():
                if c.numero == num:
                    cons[num] = c.id

    print("[DEMO] Recepcionista...")
    try:
        r = registro.registrar_empleado(
            ci="5559999", nombre="Sofia", apellido="Vaca",
            tipo_empleado="recepcionista", telefono="77750000",
            turno="Mañana", area="Recepción general"
        )
        print(f"       Recepcionista -> usuario: {r['username']} / contraseña: {r['password']}")
    except ValueError as e:
        print(f"       (Omitido) {e}")

    print("[DEMO] Doctores (atienden todos los días)...")
    doctores = [
        ("4567001", "Juan", "Pérez", "Cardiología", "1"),
        ("4567002", "Maria", "López", "Pediatría", "2"),
        ("4567003", "Carlos", "Soto", "Odontología", "3"),
    ]
    for ci, nombre, apellido, especialidad, num_cons in doctores:
        try:
            res = registro.registrar_empleado(
                ci=ci, nombre=nombre, apellido=apellido, tipo_empleado="doctor",
                telefono="777000", especialidad_id=esp[especialidad],
                email=f"{nombre.lower()}@clinica.bo"
            )
            doc = Doctor.buscar_por_usuario_id(_uid(res["username"]))
            for dia in range(7):
                HorarioTrabajo.agregar(doc.id, cons[num_cons], dia, "08:00", "18:00")
            print(f"       Dr(a). {nombre} {apellido} -> usuario: {res['username']} / contraseña: {res['password']}")
        except ValueError as e:
            print(f"       (Omitido {nombre}) {e}")


def _uid(username):
    from models import Usuario
    return Usuario.buscar_por_username(username).id


if __name__ == "__main__":
    print("[DEMO] Cargando datos de demostración...")
    cargar()
    print("[DEMO] Listo.")
