# registro_operaciones.py
import os
import MetaTrader5 as mt5
import csv
from datetime import datetime, timedelta

# Ruta del archivo CSV de operaciones
OPERACIONES_CSV = os.path.join(os.path.dirname(__file__), 'operaciones_trading.csv')

# Diccionario global para mapear tickets de órdenes abiertas a su información
# Esto permite registrar la estrategia y otros detalles una vez que la orden se cierra
ordenes_en_curso = {}

def registrar_operacion_abierta(ticket, simbolo, estrategia, lote, tipo, precio_apertura, sl, tp):
    """
    Registra una operación recién abierta en una variable global para posterior seguimiento.
    """
    ordenes_en_curso[ticket] = {
        'simbolo': simbolo,
        'estrategia': estrategia,
        'lote': lote,
        'tipo': tipo,  # Ya viene como 'compra' o 'venta'
        'precio_apertura': precio_apertura,
        'stop_loss': sl,
        'take_profit': tp,
        'fecha_apertura': datetime.now()
    }

def cargar_tickets_existentes():
    """Carga los tickets de las operaciones ya registradas para evitar duplicados."""
    tickets = set()
    if os.path.isfile(OPERACIONES_CSV):
        with open(OPERACIONES_CSV, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader, None)  # Saltar la cabecera
            for fila in reader:
                if len(fila) > 0:
                    try:
                        tickets.add(int(fila[0]))  # Suponiendo que el ticket está en la primera columna
                    except (ValueError, IndexError):
                        continue
    return tickets

def monitorear_y_registrar_operaciones_cerradas(gestor_riesgo_global=None):
    """
    Monitorea las operaciones cerradas y las registra en el archivo CSV sin duplicados.
    Acepta una instancia del gestor de riesgo para registrar las operaciones.
    """
    tickets_registrados = cargar_tickets_existentes()
    
    # Obtener el historial de deals (cierres) del día para buscar operaciones cerradas
    deals_historial = mt5.history_deals_get(datetime.now() - timedelta(days=1), datetime.now())
    
    if deals_historial is None:
        return
        
    for deal in deals_historial:
        if deal.order in ordenes_en_curso and deal.order not in tickets_registrados:
            # Es una operación de nuestro agente que se acaba de cerrar y no ha sido registrada
            info_operacion = ordenes_en_curso[deal.order]
            
            # Calcular resultado y pips
            precio_cierre = deal.price
            
            info_simbolo = mt5.symbol_info(deal.symbol)
            if info_simbolo is None: continue
            punto = info_simbolo.point
            
            if deal.type == mt5.DEAL_TYPE_BUY:
                resultado_dinero = (precio_cierre - info_operacion['precio_apertura']) * deal.volume * 100000
                resultado_pips = (precio_cierre - info_operacion['precio_apertura']) / punto
            else:  # Venta
                resultado_dinero = (info_operacion['precio_apertura'] - precio_cierre) * deal.volume * 100000
                resultado_pips = (info_operacion['precio_apertura'] - precio_cierre) / punto

            operacion_cerrada = {
                'ticket_mt5': deal.order,
                'simbolo': deal.symbol,
                'estrategia': info_operacion['estrategia'],
                'fecha_apertura': info_operacion['fecha_apertura'].strftime('%Y-%m-%d %H:%M:%S'),
                'fecha_cierre': datetime.fromtimestamp(deal.time).strftime('%Y-%m-%d %H:%M:%S'),
                'tipo': info_operacion['tipo'],
                'precio_apertura': info_operacion['precio_apertura'],
                'precio_cierre': precio_cierre,
                'resultado_dinero': resultado_dinero,
                'resultado_pips': resultado_pips,
                'stop_loss': info_operacion['stop_loss'],
                'take_profit': info_operacion['take_profit'],
                'lote': deal.volume,
                'comentario': deal.comment
            }
            
            # Escribir en el CSV
            with open(OPERACIONES_CSV, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=operacion_cerrada.keys())
                if f.tell() == 0:  # Escribir la cabecera si el archivo está vacío
                    writer.writeheader()
                writer.writerow(operacion_cerrada)
            
            print(f"✅ Operación {deal.order} de {deal.symbol} registrada en CSV.")
            
            # NUEVO: Registrar la operación en el gestor de riesgo global
            if gestor_riesgo_global:
                gestor_riesgo_global.registrar_operacion(info_operacion['estrategia'], resultado_dinero)
                
            # Eliminar del seguimiento una vez registrada
            del ordenes_en_curso[deal.order]