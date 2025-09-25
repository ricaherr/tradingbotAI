#!/usr/bin/env python3
"""
Monitor de progreso de optimización en tiempo real.
"""

import time
import subprocess
import os

def check_optimization_status():
    """Verifica el estado de la optimización."""
    try:
        # Verificar procesos activos
        result = subprocess.run(
            ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'commandline,processid', '/format:list'],
            capture_output=True, text=True, shell=True
        )
        
        optimization_processes = []
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if 'run_optimization' in line:
                optimization_processes.append(line.strip())
        
        return len(optimization_processes)
    except:
        return 0

def monitor_files():
    """Monitorea archivos de resultados."""
    files_to_watch = [
        'convergence_plot.png',
        'optimization_results.json',
        'best_results.csv'
    ]
    
    file_times = {}
    for file in files_to_watch:
        if os.path.exists(file):
            file_times[file] = os.path.getmtime(file)
    
    return file_times

def main():
    print("=== MONITOR DE OPTIMIZACIÓN ===")
    print("Presiona Ctrl+C para salir\n")
    
    start_time = time.time()
    last_file_times = monitor_files()
    
    try:
        while True:
            # Verificar procesos
            active_processes = check_optimization_status()
            elapsed = time.time() - start_time
            
            print(f"\r[{elapsed/60:.1f}m] Procesos activos: {active_processes}", end="", flush=True)
            
            # Verificar archivos nuevos
            current_file_times = monitor_files()
            for file, mtime in current_file_times.items():
                if file not in last_file_times or mtime > last_file_times[file]:
                    print(f"\n[NUEVO] {file} actualizado")
            
            last_file_times = current_file_times
            
            if active_processes == 0:
                print("\n\n[INFO] No hay procesos de optimización activos")
                break
                
            time.sleep(10)  # Verificar cada 10 segundos
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Monitor detenido por el usuario")

if __name__ == "__main__":
    main()