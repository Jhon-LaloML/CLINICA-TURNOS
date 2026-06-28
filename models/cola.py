"""
Estructura de Datos: Cola (FIFO)
================================
Implementación manual con lista. Materia: Estructura de Datos 1.
El primero en entrar es el primero en salir (fila de espera real).
"""


class Cola:
    def __init__(self):
        self._items = []

    def encolar(self, elemento):
        """Agrega al final. O(1)."""
        self._items.append(elemento)

    def desencolar(self):
        """Saca y devuelve el primero. O(n). None si vacía."""
        if self.esta_vacia():
            return None
        return self._items.pop(0)

    def frente(self):
        """Mira el primero sin sacarlo. None si vacía."""
        if self.esta_vacia():
            return None
        return self._items[0]

    def esta_vacia(self):
        return len(self._items) == 0

    def tamano(self):
        return len(self._items)

    def listar(self):
        """Copia en orden (frente primero), sin modificar la cola."""
        return list(self._items)

    def __len__(self):
        return self.tamano()

    def __iter__(self):
        return iter(self._items)

    def __repr__(self):
        return f"Cola({self._items})"
