# registro_operaciones.py
import os
import MetaTrader5 as mt5
import csv
from datetime import datetime, timedelta
from estrategia_ia.utils.error_handler import safe_execute
from estrategia_ia.utils.logger import broker_logger

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

def _calcular_resultado_operacion(deal, info_operacion):
    """Calcula el resultado en dinero y pips de una operación cerrada."""
    info_simbolo = mt5.symbol_info(deal.symbol)
    if info_simbolo is None:
        return None, None
    
    precio_cierre = deal.price
    punto = info_simbolo.point
    
    if deal.type == mt5.DEAL_TYPE_BUY:
        resultado_dinero = (precio_cierre - info_operacion['precio_apertura']) * deal.volume * 100000
        resultado_pips = (precio_cierre - info_operacion['precio_apertura']) / punto
    else:  # Venta
        resultado_dinero = (info_operacion['precio_apertura'] - precio_cierre) * deal.volume * 100000
        resultado_pips = (info_operacion['precio_apertura'] - precio_cierre) / punto
    
    return resultado_dinero, resultado_pips

def _crear_registro_operacion(deal, info_operacion, resultado_dinero, resultado_pips):
    """Crea el diccionario con los datos de la operación cerrada."""
    return {
        'ticket_mt5': deal.order,
        'simbolo': deal.symbol,
        'estrategia': info_operacion['estrategia'],
        'fecha_apertura': info_operacion['fecha_apertura'].strftime('%Y-%m-%d %H:%M:%S'),
        'fecha_cierre': datetime.fromtimestamp(deal.time).strftime('%Y-%m-%d %H:%M:%S'),
        'tipo': info_operacion['tipo'],
        'precio_apertura': info_operacion['precio_apertura'],
        'precio_cierre': deal.price,
        'resultado_dinero': resultado_dinero,
        'resultado_pips': resultado_pips,
        'stop_loss': info_operacion['stop_loss'],
        'take_profit': info_operacion['take_profit'],
        'lote': deal.volume,
        'comentario': deal.comment
    }

def _escribir_operacion_csv(operacion_cerrada):
    """Escribe una operación al archivo CSV de forma segura."""
    def write_to_csv():
        with open(OPERACIONES_CSV, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=operacion_cerrada.keys())
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(operacion_cerrada)
    
    return safe_execute(write_to_csv, default_return=False, log_errors=True)

def _procesar_operacion_cerrada(deal, info_operacion, gestor_riesgo_global):
    """Procesa una operación cerrada individual."""
    resultado_dinero, resultado_pips = _calcular_resultado_operacion(deal, info_operacion)
    if resultado_dinero is None:
        return False
    
    operacion_cerrada = _crear_registro_operacion(deal, info_operacion, resultado_dinero, resultado_pips)
    
    if not _escribir_operacion_csv(operacion_cerrada):
        broker_logger.error(f"No se pudo escribir operación {deal.order} al CSV")
        return False
    
    print(f"✅ Operación {deal.order} de {deal.symbol} registrada en CSV.")
    
    if gestor_riesgo_global:
        gestor_riesgo_global.registrar_operacion(info_operacion['estrategia'], resultado_dinero)
    
    return True

def monitorear_y_registrar_operaciones_cerradas(gestor_riesgo_global=None):
    """Monitorea las operaciones cerradas y las registra en el archivo CSV sin duplicados."""
    tickets_registrados = cargar_tickets_existentes()
    deals_historial = mt5.history_deals_get(datetime.now() - timedelta(days=1), datetime.now())
    
    if deals_historial is None:
        return
    
    for deal in deals_historial:
        if deal.order in ordenes_en_curso and deal.order not in tickets_registrados:
            info_operacion = ordenes_en_curso[deal.order]
            
            if _procesar_operacion_cerrada(deal, info_operacion, gestor_riesgo_global):
                del ordenes_en_curso[deal.order]