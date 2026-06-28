"""
Inicializa la BD y crea el usuario admin + la clínica.
Ejecutar una sola vez: python seed.py
"""
from models import inicializar_db, Usuario
from models.database import obtener_conexion


def crear_clinica():
    conexion = obtener_conexion()
    existe = conexion.execute("SELECT id FROM clinica LIMIT 1").fetchone()
    if not existe:
        conexion.execute(
            "INSERT INTO clinica (nombre, direccion, telefono) VALUES (?, ?, ?)",
            ("Clínica San Gabriel", "Av. Principal #123, Santa Cruz", "(3) 333-4567")
        )
        conexion.commit()
        print("[SEED] Clínica creada.")
    conexion.close()


def crear_admin():
    if Usuario.buscar_por_username("admin"):
        print("[SEED] El usuario admin ya existe.")
    else:
        Usuario.crear("admin", "admin123", "admin")
        print("[SEED] Admin creado -> usuario: admin / contraseña: admin123")


if __name__ == "__main__":
    print("[SEED] Inicializando base de datos...")
    inicializar_db()
    crear_clinica()
    crear_admin()
    print("[SEED] Listo.")
