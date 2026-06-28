"""
Estructura de Datos: Pila (LIFO)
================================
Implementación manual con lista. Materia: Estructura de Datos 1.
El último en entrar es el primero en salir (historial: último atendido arriba).
"""


class Pila:
    def __init__(self):
        self._items = []

    def apilar(self, elemento):
        """Pone en el tope. O(1)."""
        self._items.append(elemento)

    def desapilar(self):
        """Saca y devuelve el del tope. O(1). None si vacía."""
        if self.esta_vacia():
            return None
        return self._items.pop()

    def tope(self):
        """Mira el del tope sin sacarlo. None si vacía."""
        if self.esta_vacia():
            return None
        return self._items[-1]

    def esta_vacia(self):
        return len(self._items) == 0

    def tamano(self):
        return len(self._items)

    def listar_desde_tope(self):
        """Copia desde el tope (más reciente primero)."""
        return list(reversed(self._items))

    def __len__(self):
        return self.tamano()

    def __iter__(self):
        return iter(reversed(self._items))

    def __repr__(self):
        return f"Pila({self._items})"
