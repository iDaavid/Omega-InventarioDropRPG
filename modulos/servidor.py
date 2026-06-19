from collections import deque

class ServidorRPG:
    def __init__(self):
        # Inicializar cola de eventos
        self.cola_eventos = deque()
        print("[Servidor] Iniciado y esperando eventos...")

    def encolar_evento(self, evento):
        # Agregar evento al final de la cola
        self.cola_eventos.append(evento)
        print(f"[Servidor] Evento encolado: '{evento}'")

    def procesar_siguiente(self):
        # Verificacion
        if not self.cola_eventos:
            print("[Servidor] La cola está vacía. No hay eventos por procesar.")
            return None
        
        # Remover el evento mas viejo
        evento_actual = self.cola_eventos.popleft()
        print(f"[Servidor] Procesando evento: '{evento_actual}'")
        return evento_actual

# Pruebas (no se ejecuta si se usa en el main)
if __name__ == "__main__":
    mi_servidor = ServidorRPG()
    mi_servidor.encolar_evento("Atacar Jefe")
    mi_servidor.encolar_evento("Usar Poción")
    
    print("-" * 30)
    
    mi_servidor.procesar_siguiente()
    mi_servidor.procesar_siguiente()
    mi_servidor.procesar_siguiente() # Intento extra a ver si esta vacia