# strategies.py

def determinar_senales(df, estrategia):
    """
    Identifica las señales de compra o venta basadas en el nombre de la estrategia.
    """
    ultima_vela = df.iloc[-1]
    
    if len(df) < 2:
        return None

    nombre_estrategia = estrategia.get("nombre")

    # Lógica para la estrategia 'Cruce EMA + Vela Elefante'
    if nombre_estrategia == "Cruce EMA + Vela Elefante":
        if not all(k in df.columns for k in ['EMA_9', 'EMA_20', 'es_vela_elefante']):
            return None

        cruce_alcista = df['EMA_9'].iloc[-2] < df['EMA_20'].iloc[-2] and ultima_vela['EMA_9'] > ultima_vela['EMA_20']
        cruce_bajista = df['EMA_9'].iloc[-2] > df['EMA_20'].iloc[-2] and ultima_vela['EMA_9'] < ultima_vela['EMA_20']
        es_elefante = ultima_vela['es_vela_elefante']
        
        if cruce_alcista and es_elefante:
            return "compra"
        elif cruce_bajista and es_elefante:
            return "venta"

    # Lógica para la estrategia 'Rompimiento de la EMA 20'
    elif nombre_estrategia == "Rompimiento de la EMA 20":
        if not all(k in df.columns for k in ['EMA_20', 'es_vela_elefante']):
            return None
        
        es_elefante = ultima_vela['es_vela_elefante']
        
        if es_elefante:
            rompimiento_alcista = ultima_vela['close'] > ultima_vela['EMA_20'] and df['close'].iloc[-2] < df['EMA_20'].iloc[-2]
            if rompimiento_alcista:
                return "compra"

            rompimiento_bajista = ultima_vela['close'] < ultima_vela['EMA_20'] and df['close'].iloc[-2] > df['EMA_20'].iloc[-2]
            if rompimiento_bajista:
                return "venta"
    
    # Lógica para la estrategia 'Reversión a la Media'
    elif nombre_estrategia == "Reversión a la Media":
        criterios = estrategia.get("criterios", {})
        if 'EMA_20' not in df.columns:
            return None
        
        precio_sobre_ema200 = True
        precio_bajo_ema200 = True
        if criterios.get("usar_filtro_tendencia_200_ema", False):
            if 'EMA_200' not in df.columns or len(df) < 200:
                print("No hay suficientes datos para la EMA de 200. Desactivando filtro de tendencia.")
            else:
                precio_sobre_ema200 = ultima_vela['close'] > ultima_vela['EMA_200']
                precio_bajo_ema200 = ultima_vela['close'] < ultima_vela['EMA_200']
        
        cruce_alcista = df['close'].iloc[-2] < df['EMA_20'].iloc[-2] and ultima_vela['close'] > ultima_vela['EMA_20']
        if cruce_alcista and precio_sobre_ema200:
            return "compra"

        cruce_bajista = df['close'].iloc[-2] > df['EMA_20'].iloc[-2] and ultima_vela['close'] < ultima_vela['EMA_20']
        if cruce_bajista and precio_bajo_ema200:
            return "venta"

    return None