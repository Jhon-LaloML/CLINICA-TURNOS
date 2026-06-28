# Sistema de Gestión de Turnos para Clínica (versión con herencia)

Proyecto de Feria Científica — Estructura de Datos 1 — FICCT UAGRM

## Novedades de esta versión

- Base de datos con HERENCIA: PERSONA → CLIENTE / EMPLEADO → DOCTOR / RECEPCIONISTA.
- Login unificado para todos los roles (admin, recepcionista, doctor, cliente).
  Usuario inicial = primer nombre, contraseña = CI. Cada uno puede cambiarlos luego.
- El ADMIN registra empleados (doctores con especialidad, o recepcionistas),
  crea especialidades, consultorios y horarios.
- La RECEPCIONISTA registra clientes y genera fichas (con prioridad).
- El DOCTOR es quien mueve la cola (llamar, atender, ausente). La recepción no.
- El CLIENTE entra con su login y ve: información de la clínica, su ficha,
  a qué consultorio ir, y cuántas personas hay delante de él en ESA cola.
- Historial de atención por cliente (con diagnóstico del doctor).
- Ya NO hay pantalla pública tipo TV.

## Requisitos
- Python 3.10 o superior
- pip

## Instalación

```bash
pip install -r requirements.txt
python seed.py        # crea BD + clínica + admin
python seed_demo.py   # (opcional) especialidades, consultorios, doctores, recepcionista
python app.py
```

Abrir: http://localhost:8000

## Credenciales

| Usuario | Contraseña | Rol           |
|---------|-----------|---------------|
| admin   | admin123  | Administrador |

Con datos demo cargados:

| Usuario | Contraseña | Rol           |
|---------|-----------|---------------|
| sofia   | 5559999   | Recepcionista |
| juan    | 4567001   | Doctor (Cardiología) |
| maria   | 4567002   | Doctor (Pediatría) |
| carlos  | 4567003   | Doctor (Odontología) |

Los clientes se registran desde recepción (usuario = primer nombre, contraseña = CI).

## Estructuras de datos (lo central para la materia)

Implementadas a mano en `models/`:
- **Cola FIFO** (cola.py): filas de espera regular y prioritaria por consultorio.
- **Pila LIFO** (pila.py): historial de atención por consultorio.

El gestor (`gestor_turnos.py`) mantiene por consultorio: una cola regular,
una cola prioritaria y una pila de historial. La recepción ENCOLA; el doctor
DESENCOLA (prioritaria primero) y APILA en el historial. Persistencia: las
colas/pilas se reconstruyen desde SQLite al reiniciar.

## Estructura de la base de datos (herencia)

```
USUARIO (login: username, password_hash, rol)
PERSONA (ci, nombre, apellido, telefono, tipo) --(usuario_id)--> USUARIO
  ├── CLIENTE (persona_id)
  └── EMPLEADO (persona_id, codigo_empleado, direccion, estado, tipo)
        ├── DOCTOR (empleado_id, especialidad_id, email)
        └── RECEPCIONISTA (empleado_id, turno, area)
CLINICA, CONSULTORIO (clinica_id), ESPECIALIDAD
HORARIO_TRABAJO (doctor_id, consultorio_id, dia_semana, hora_inicio, hora_fin)
FICHA_ATENCION (cliente_id, doctor_id, recepcionista_id, consultorio_id,
                codigo, tipo, estado, motivo, diagnostico, horas)
```

## Roles y permisos

- **admin**: especialidades, consultorios, empleados, horarios.
- **recepcionista**: registra clientes y genera fichas.
- **doctor**: mueve su cola (llamar, atender, ausente, cerrar).
- **cliente**: ve la clínica, su ficha, su cola y su historial.
