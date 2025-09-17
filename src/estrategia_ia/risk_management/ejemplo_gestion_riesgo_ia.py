# ejemplo_gestion_riesgo_ia.py
from gestion_riesgo import GestionRiesgo
import random

# Configuración inicial
limites_estrategias = {'estrategia1': 100, 'estrategia2': 150}
riesgo = GestionRiesgo(
    limite_global=300,
    limites_estrategias=limites_estrategias.copy(),
    modo_porcentaje=False,
    cooldown_activo=True,
    cooldown_minutos=30,
    reducir_posicion_activo=True,
    perdidas_consecutivas_reduccion=2,
    factor_reduccion=0.7,
    limite_perdidas_consecutivas_activo=True,
    limite_perdidas_consecutivas=3
)

# Historial de resultados recientes por estrategia
historial = {'estrategia1': [], 'estrategia2': []}

# Función IA simple: ajusta límites según desempeño reciente

def ajustar_limites(riesgo, historial, ventana=5, factor_ajuste=1.2, factor_reduccion=0.8):
    for estrategia, resultados in historial.items():
        if len(resultados) < ventana:
            continue
        suma = sum(resultados[-ventana:])
        if suma > 0:
            # Si la suma de los últimos resultados es positiva, sube el límite
            riesgo.limites_estrategias[estrategia] *= factor_ajuste
        elif suma < 0:
            # Si es negativa, baja el límite
            riesgo.limites_estrategias[estrategia] *= factor_reduccion
        # Limita el rango de los límites
        riesgo.limites_estrategias[estrategia] = max(50, min(riesgo.limites_estrategias[estrategia], 500))

# Simulación de operaciones
def simular_operaciones(n=20):
    for i in range(n):
        for estrategia in ['estrategia1', 'estrategia2']:
            if not riesgo.puede_operar(estrategia):
                print(f"[{estrategia}] No puede operar (límite alcanzado o cooldown)")
                continue
            # Simula resultado aleatorio
            resultado = random.choice([random.uniform(-60, 80), random.uniform(-30, 40)])
            historial[estrategia].append(resultado)
            riesgo.registrar_operacion(estrategia, resultado)
            print(f"[{estrategia}] Resultado: {resultado:.2f} | Límite actual: {riesgo.limites_estrategias[estrategia]:.2f}")
        # Ajuste IA cada 5 operaciones
        if i % 5 == 0 and i > 0:
            ajustar_limites(riesgo, historial)
            print("\n--- Ajuste IA de límites ---")
            print(riesgo.limites_estrategias)
            print("--------------------------\n")
    print("\nResumen final:")
    print(riesgo.resumen())

if __name__ == "__main__":
    simular_operaciones()
