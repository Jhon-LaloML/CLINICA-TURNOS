"""
Gestor de Turnos (en memoria) — CORAZÓN para Estructura de Datos 1
==================================================================

Mantiene en memoria, POR CONSULTORIO:
  - colas_regular     { consultorio_id: Cola() }   (FIFO)
  - colas_prioritaria { consultorio_id: Cola() }   (FIFO)
  - historial         { consultorio_id: Pila() }   (LIFO)
  - actual            { consultorio_id: item }      paciente en atención
  - estado            { consultorio_id: str }       atendiendo|no_recibe|finalizado

Flujo:
  recepción genera ficha -> encolar_ficha()
  doctor llama siguiente -> llamar_siguiente()  (desencola, prioritaria primero)
  doctor marca atendido  -> marcar_atendido()   (apila en historial)
  doctor cierra          -> cerrar_inscripciones()

Persistencia: al iniciar, reconstruye las colas/pilas desde las fichas de hoy.
"""

from datetime import date

from .cola import Cola
from .pila import Pila
from .database import obtener_conexion

ESTADO_ATENDIENDO = "atendiendo"
ESTADO_NO_RECIBE = "no_recibe"
ESTADO_FINALIZADO = "finalizado"


class GestorTurnos:
    def __init__(self):
        self.colas_regular = {}
        self.colas_prioritaria = {}
        self.historial = {}
        self.actual = {}
        self.estado = {}
        self._reconstruir()

    def _reconstruir(self):
        self.colas_regular = {}
        self.colas_prioritaria = {}
        self.historial = {}
        self.actual = {}
        self.estado = {}
        hoy = date.today().isoformat()
        try:
            conexion = obtener_conexion()
            filas = conexion.execute("""
                SELECT f.id, f.codigo, f.tipo, f.consultorio_id, f.motivo, f.estado,
                       f.hora_registro,
                       p.nombre || ' ' || p.apellido AS cliente_nombre,
                       p.ci AS cliente_ci
                FROM ficha_atencion f
                JOIN cliente cl ON f.cliente_id = cl.id
                JOIN persona p  ON cl.persona_id = p.id
                WHERE date(f.hora_registro) = ?
                ORDER BY f.hora_registro
            """, (hoy,)).fetchall()
            conexion.close()
        except Exception:
            return

        for f in filas:
            item = {
                "ficha_id": f["id"], "codigo": f["codigo"], "tipo": f["tipo"],
                "consultorio_id": f["consultorio_id"], "motivo": f["motivo"],
                "cliente_nombre": f["cliente_nombre"], "cliente_ci": f["cliente_ci"],
                "hora_registro": f["hora_registro"],
            }
            est = f["estado"]
            if est == "en_espera":
                self._encolar(item)
            elif est == "atendiendo":
                self.actual[item["consultorio_id"]] = item
            elif est in ("atendido", "ausente"):
                item["estado_final"] = est
                self.historial.setdefault(item["consultorio_id"], Pila()).apilar(item)

    def recargar(self):
        self._reconstruir()

    def _encolar(self, item):
        cid = item["consultorio_id"]
        if item["tipo"] == "prioritario":
            self.colas_prioritaria.setdefault(cid, Cola()).encolar(item)
        else:
            self.colas_regular.setdefault(cid, Cola()).encolar(item)

    def encolar_ficha(self, ficha):
        item = {
            "ficha_id": ficha.id, "codigo": ficha.codigo, "tipo": ficha.tipo,
            "consultorio_id": ficha.consultorio_id, "motivo": ficha.motivo,
            "cliente_nombre": ficha.cliente_nombre, "cliente_ci": ficha.cliente_ci,
            "hora_registro": ficha.hora_registro,
        }
        self._encolar(item)

    def puede_recibir(self, cid):
        return self.estado.get(cid, ESTADO_ATENDIENDO) == ESTADO_ATENDIENDO

    # Consultas
    def cola_regular(self, cid):
        c = self.colas_regular.get(cid)
        return c.listar() if c else []

    def cola_prioritaria(self, cid):
        c = self.colas_prioritaria.get(cid)
        return c.listar() if c else []

    def cantidad_en_espera(self, cid):
        r = self.colas_regular.get(cid)
        p = self.colas_prioritaria.get(cid)
        return (r.tamano() if r else 0) + (p.tamano() if p else 0)

    def proximo_de(self, cid):
        p = self.colas_prioritaria.get(cid)
        if p and not p.esta_vacia():
            return p.frente()
        r = self.colas_regular.get(cid)
        if r and not r.esta_vacia():
            return r.frente()
        return None

    def paciente_actual(self, cid):
        return self.actual.get(cid)

    def estado_consultorio(self, cid):
        return self.estado.get(cid, ESTADO_ATENDIENDO)

    # Operaciones del doctor
    def llamar_siguiente(self, cid):
        sig = self._desencolar(cid)
        if sig is None:
            return None
        self.actual[cid] = sig
        return sig

    def _desencolar(self, cid):
        p = self.colas_prioritaria.get(cid)
        if p and not p.esta_vacia():
            return p.desencolar()
        r = self.colas_regular.get(cid)
        if r and not r.esta_vacia():
            return r.desencolar()
        return None

    def marcar_atendido(self, cid):
        actual = self.actual.get(cid)
        if actual is None:
            return None
        actual["estado_final"] = "atendido"
        self.historial.setdefault(cid, Pila()).apilar(actual)
        self.actual[cid] = None
        self._verificar_fin(cid)
        return actual

    def marcar_ausente(self, cid):
        actual = self.actual.get(cid)
        if actual is None:
            return None
        actual["estado_final"] = "ausente"
        self.historial.setdefault(cid, Pila()).apilar(actual)
        self.actual[cid] = None
        self._verificar_fin(cid)
        return actual

    def cerrar_inscripciones(self, cid):
        self.estado[cid] = ESTADO_NO_RECIBE
        self._verificar_fin(cid)

    def reabrir_inscripciones(self, cid):
        self.estado[cid] = ESTADO_ATENDIENDO

    def _verificar_fin(self, cid):
        if self.estado.get(cid) == ESTADO_NO_RECIBE:
            if self.cantidad_en_espera(cid) == 0 and self.actual.get(cid) is None:
                self.estado[cid] = ESTADO_FINALIZADO

    # Historial
    def historial_de(self, cid, limite=None):
        pila = self.historial.get(cid)
        if pila is None:
            return []
        items = pila.listar_desde_tope()
        return items[:limite] if limite else items

    def cantidad_atendidos(self, cid):
        pila = self.historial.get(cid)
        return pila.tamano() if pila else 0

    # Para la vista del cliente
    def posicion_en_cola(self, cid, ficha_id):
        prioritaria = self.cola_prioritaria(cid)
        regular = self.cola_regular(cid)
        for i, item in enumerate(prioritaria):
            if item["ficha_id"] == ficha_id:
                return i
        for i, item in enumerate(regular):
            if item["ficha_id"] == ficha_id:
                return len(prioritaria) + i
        return None


gestor = GestorTurnos()
