"""
Módulo de Base de Datos (SQLite)
=================================

Implementa la estructura del diagrama entidad-relación con herencia:

    PERSONA  (datos comunes: ci, nombre, apellido, telefono, tipo)
      ├── CLIENTE      (persona_id)
      └── EMPLEADO     (persona_id, codigo, direccion, estado)
            ├── DOCTOR        (empleado_id, especialidad_id)
            └── RECEPCIONISTA (empleado_id, turno, area)

Más: USUARIO (login), CLINICA, CONSULTORIO, ESPECIALIDAD,
HORARIO_TRABAJO y FICHA_ATENCION.

Los datos maestros viven aquí (SQLite). El flujo dinámico de turnos
(colas y pilas) vive en memoria (gestor_turnos.py).
"""

import sqlite3
import os

if os.environ.get("RENDER"):
    RUTA_DB = "/tmp/clinica.db"
else:
    RUTA_DB = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "clinica.db"
    )
    os.makedirs(os.path.dirname(RUTA_DB), exist_ok=True)

def obtener_conexion():
    """Abre una conexión SQLite con filas accesibles por nombre."""
    conexion = sqlite3.connect(RUTA_DB)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar_db():
    """Crea todas las tablas si no existen."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # ----------------------------------------------------------------
    # CLINICA
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clinica (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT NOT NULL,
            direccion TEXT,
            telefono  TEXT
        )
    """)

    # ----------------------------------------------------------------
    # USUARIO (login para todos los roles)
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            rol           TEXT NOT NULL CHECK(rol IN ('admin','recepcionista','doctor','cliente')),
            activo        INTEGER NOT NULL DEFAULT 1,
            fecha_creacion TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # ----------------------------------------------------------------
    # PERSONA (tabla padre de la herencia)
    # tipo: 'cliente' o 'empleado' (discriminador del primer nivel)
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS persona (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER UNIQUE,
            ci         TEXT NOT NULL UNIQUE,
            nombre     TEXT NOT NULL,
            apellido   TEXT NOT NULL,
            telefono   TEXT,
            tipo       TEXT NOT NULL CHECK(tipo IN ('cliente','empleado')),
            FOREIGN KEY (usuario_id) REFERENCES usuario(id) ON DELETE SET NULL
        )
    """)

    # ----------------------------------------------------------------
    # ESPECIALIDAD
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS especialidad (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL UNIQUE,
            descripcion TEXT
        )
    """)

    # ----------------------------------------------------------------
    # CONSULTORIO
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultorio (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            clinica_id INTEGER,
            numero     TEXT NOT NULL UNIQUE,
            ubicacion  TEXT,
            FOREIGN KEY (clinica_id) REFERENCES clinica(id) ON DELETE SET NULL
        )
    """)

    # ----------------------------------------------------------------
    # CLIENTE (hija de PERSONA)
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cliente (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (persona_id) REFERENCES persona(id) ON DELETE CASCADE
        )
    """)

    # ----------------------------------------------------------------
    # EMPLEADO (hija de PERSONA)
    # tipo: 'doctor' o 'recepcionista' (discriminador del segundo nivel)
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empleado (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id      INTEGER NOT NULL UNIQUE,
            codigo_empleado TEXT UNIQUE,
            direccion       TEXT,
            estado          TEXT DEFAULT 'activo',
            tipo            TEXT NOT NULL CHECK(tipo IN ('doctor','recepcionista')),
            FOREIGN KEY (persona_id) REFERENCES persona(id) ON DELETE CASCADE
        )
    """)

    # ----------------------------------------------------------------
    # DOCTOR (hija de EMPLEADO)
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id     INTEGER NOT NULL UNIQUE,
            especialidad_id INTEGER NOT NULL,
            email           TEXT,
            FOREIGN KEY (empleado_id)     REFERENCES empleado(id)     ON DELETE CASCADE,
            FOREIGN KEY (especialidad_id) REFERENCES especialidad(id) ON DELETE RESTRICT
        )
    """)

    # ----------------------------------------------------------------
    # RECEPCIONISTA (hija de EMPLEADO)
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recepcionista (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER NOT NULL UNIQUE,
            turno       TEXT,
            area        TEXT,
            FOREIGN KEY (empleado_id) REFERENCES empleado(id) ON DELETE CASCADE
        )
    """)

    # ----------------------------------------------------------------
    # HORARIO_TRABAJO
    # dia_semana: 0=lunes ... 6=domingo
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS horario_trabajo (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id      INTEGER NOT NULL,
            consultorio_id INTEGER NOT NULL,
            dia_semana     INTEGER NOT NULL CHECK(dia_semana BETWEEN 0 AND 6),
            hora_inicio    TEXT NOT NULL,
            hora_fin       TEXT NOT NULL,
            FOREIGN KEY (doctor_id)      REFERENCES doctor(id)      ON DELETE CASCADE,
            FOREIGN KEY (consultorio_id) REFERENCES consultorio(id) ON DELETE CASCADE
        )
    """)

    # ----------------------------------------------------------------
    # FICHA_ATENCION (el "ticket")
    # ----------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ficha_atencion (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id       INTEGER NOT NULL,
            doctor_id        INTEGER,
            recepcionista_id INTEGER,
            consultorio_id   INTEGER NOT NULL,
            numero_ficha     INTEGER NOT NULL,
            codigo           TEXT NOT NULL,
            tipo             TEXT NOT NULL CHECK(tipo IN ('regular','prioritario')),
            estado           TEXT NOT NULL DEFAULT 'en_espera'
                             CHECK(estado IN ('en_espera','atendiendo','atendido','ausente')),
            motivo           TEXT,
            diagnostico      TEXT,
            hora_registro    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            hora_atencion    TEXT,
            FOREIGN KEY (cliente_id)       REFERENCES cliente(id)       ON DELETE CASCADE,
            FOREIGN KEY (doctor_id)        REFERENCES doctor(id)        ON DELETE SET NULL,
            FOREIGN KEY (recepcionista_id) REFERENCES recepcionista(id) ON DELETE SET NULL,
            FOREIGN KEY (consultorio_id)   REFERENCES consultorio(id)   ON DELETE RESTRICT
        )
    """)

    conexion.commit()
    conexion.close()
    print("[DB] Tablas creadas/verificadas correctamente.")


if __name__ == "__main__":
    inicializar_db()
