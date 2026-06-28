"""
Modelo Ficha (ficha_atencion)
=============================

La ficha es el "ticket". Código formato C{consultorio}-{numero},
correlativo por consultorio por día (ej. C1-005).

Registro permanente en SQLite; la posición en cola vive en memoria (gestor).
"""

from datetime import date
from .database import obtener_conexion


class Ficha:
    def __init__(self, id, codigo, numero_ficha, cliente_id, consultorio_id,
                 tipo, estado, motivo=None, diagnostico=None, hora_registro=None, hora_atencion=None,
                 doctor_id=None, recepcionista_id=None,
                 cliente_nombre=None, cliente_ci=None, consultorio_numero=None):
        self.id = id
        self.codigo = codigo
        self.numero_ficha = numero_ficha
        self.cliente_id = cliente_id
        self.consultorio_id = consultorio_id
        self.tipo = tipo
        self.estado = estado
        self.motivo = motivo
        self.diagnostico = diagnostico
        self.hora_registro = hora_registro
        self.hora_atencion = hora_atencion
        self.doctor_id = doctor_id
        self.recepcionista_id = recepcionista_id
        self.cliente_nombre = cliente_nombre
        self.cliente_ci = cliente_ci
        self.consultorio_numero = consultorio_numero

    @property
    def es_prioritario(self):
        return self.tipo == "prioritario"

    @staticmethod
    def _siguiente_numero(consultorio_id, consultorio_numero):
        hoy = date.today().isoformat()
        conexion = obtener_conexion()
        n = conexion.execute("""
            SELECT COUNT(*) AS n FROM ficha_atencion
            WHERE consultorio_id = ? AND date(hora_registro) = ?
        """, (consultorio_id, hoy)).fetchone()["n"]
        conexion.close()
        numero = n + 1
        return f"C{consultorio_numero}-{numero:03d}", numero

    @staticmethod
    def crear(cliente_id, consultorio_id, consultorio_numero, tipo,
              motivo="", recepcionista_id=None):
        if tipo not in ("regular", "prioritario"):
            raise ValueError("El tipo debe ser 'regular' o 'prioritario'.")
        codigo, numero = Ficha._siguiente_numero(consultorio_id, consultorio_numero)
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO ficha_atencion
                (cliente_id, consultorio_id, recepcionista_id, numero_ficha,
                 codigo, tipo, estado, motivo)
            VALUES (?, ?, ?, ?, ?, ?, 'en_espera', ?)
        """, (cliente_id, consultorio_id, recepcionista_id, numero, codigo, tipo, motivo.strip()))
        nuevo_id = cursor.lastrowid
        conexion.commit()
        conexion.close()
        return Ficha.buscar_por_id(nuevo_id)

    _SELECT = """
        SELECT f.*,
               p.nombre || ' ' || p.apellido AS cliente_nombre,
               p.ci AS cliente_ci,
               c.numero AS consultorio_numero
        FROM ficha_atencion f
        JOIN cliente cl ON f.cliente_id = cl.id
        JOIN persona p  ON cl.persona_id = p.id
        JOIN consultorio c ON f.consultorio_id = c.id
    """

    @staticmethod
    def buscar_por_id(ficha_id):
        conexion = obtener_conexion()
        fila = conexion.execute(Ficha._SELECT + " WHERE f.id = ?", (ficha_id,)).fetchone()
        conexion.close()
        return Ficha._desde_fila(fila) if fila else None

    @staticmethod
    def ficha_activa_de_cliente(cliente_id):
        """Ficha de hoy del cliente que sigue activa (en espera o atendiendo)."""
        hoy = date.today().isoformat()
        conexion = obtener_conexion()
        fila = conexion.execute(Ficha._SELECT + """
            WHERE f.cliente_id = ? AND date(f.hora_registro) = ?
              AND f.estado IN ('en_espera','atendiendo')
            ORDER BY f.hora_registro DESC LIMIT 1
        """, (cliente_id, hoy)).fetchone()
        conexion.close()
        return Ficha._desde_fila(fila) if fila else None

    @staticmethod
    def actualizar_estado(ficha_id, nuevo_estado, registrar_atencion=False):
        conexion = obtener_conexion()
        if registrar_atencion:
            conexion.execute("""
                UPDATE ficha_atencion
                SET estado = ?, hora_atencion = datetime('now','localtime')
                WHERE id = ?
            """, (nuevo_estado, ficha_id))
        else:
            conexion.execute("UPDATE ficha_atencion SET estado = ? WHERE id = ?",
                            (nuevo_estado, ficha_id))
        conexion.commit()
        conexion.close()

    @staticmethod
    def _desde_fila(f):
        return Ficha(
            id=f["id"], codigo=f["codigo"], numero_ficha=f["numero_ficha"],
            cliente_id=f["cliente_id"], consultorio_id=f["consultorio_id"],
            tipo=f["tipo"], estado=f["estado"], motivo=f["motivo"], diagnostico=f["diagnostico"],
            hora_registro=f["hora_registro"], hora_atencion=f["hora_atencion"],
            doctor_id=f["doctor_id"], recepcionista_id=f["recepcionista_id"],
            cliente_nombre=f["cliente_nombre"], cliente_ci=f["cliente_ci"],
            consultorio_numero=f["consultorio_numero"]
        )

    def __repr__(self):
        return f"Ficha({self.codigo}, {self.tipo}, {self.estado})"

    @staticmethod
    def guardar_diagnostico(ficha_id, diagnostico):
        """El doctor puede anotar un diagnóstico/observación al atender."""
        conexion = obtener_conexion()
        conexion.execute(
            "UPDATE ficha_atencion SET diagnostico = ? WHERE id = ?",
            (diagnostico.strip(), ficha_id)
        )
        conexion.commit()
        conexion.close()

    @staticmethod
    def historial_de_cliente(cliente_id, limite=20):
        """Devuelve el historial completo de atenciones de un cliente."""
        conexion = obtener_conexion()
        filas = conexion.execute("""
            SELECT f.*,
                   p.nombre || ' ' || p.apellido AS cliente_nombre,
                   p.ci AS cliente_ci,
                   c.numero AS consultorio_numero,
                   pd.nombre || ' ' || pd.apellido AS doctor_nombre,
                   esp.nombre AS especialidad_nombre
            FROM ficha_atencion f
            JOIN cliente cl ON f.cliente_id = cl.id
            JOIN persona p  ON cl.persona_id = p.id
            JOIN consultorio c ON f.consultorio_id = c.id
            LEFT JOIN doctor d    ON f.doctor_id = d.id
            LEFT JOIN empleado e  ON d.empleado_id = e.id
            LEFT JOIN persona pd  ON e.persona_id = pd.id
            LEFT JOIN especialidad esp ON d.especialidad_id = esp.id
            WHERE f.cliente_id = ?
            ORDER BY f.hora_registro DESC
            LIMIT ?
        """, (cliente_id, limite)).fetchall()
        conexion.close()

        resultado = []
        for fila in filas:
            item = dict(fila)
            item['doctor_nombre'] = fila['doctor_nombre']
            item['especialidad_nombre'] = fila['especialidad_nombre']
            resultado.append(item)
        return resultado
