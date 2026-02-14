import os
import threading
import time
import sys
import gc
import psutil

def get_pid():
    """Получить PID процесса"""
    return os.getpid()

def get_thread_info():
    """Получить информацию о всех потоках"""
    threads = threading.enumerate()
    thread_info = []
    for thread in threads:
        thread_info.append({
            'id': thread.ident,
            'name': thread.name,
            'daemon': thread.daemon,
            'is_alive': thread.is_alive()
        })
    return thread_info

def get_memory_info(pid):
    """Получить информацию о памяти"""
    process = psutil.Process(pid)
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss,
        'vms': memory_info.vms,
        'percent': process.memory_percent()
    }

def get_process_info(pid):
    """Получить информацию о процессе"""
    process = psutil.Process(pid)
    return {
        'cpu_percent': process.cpu_percent(),
        'num_threads': process.num_threads(),
        'open_files': len(process.open_files()),
        'connections': len(process.net_connections())
    }

def detect_debugger():
    """Попытка обнаружить дебаггер"""
    debugger_detected = False
    
    # Проверка на наличие отладчиков через sys.gettrace()
    if sys.gettrace() is not None:
        debugger_detected = True
        
    # Проверка на наличие специфичных переменных отладчика
    if hasattr(sys, 'ps1'):
        debugger_detected = True
        
    # Проверка на наличие специальных атрибутов
    if '__debugger__' in globals():
        debugger_detected = True
        
    # Проверка на наличие специальных функций
    if 'pdb' in sys.modules:
        debugger_detected = True
        
    return debugger_detected

def get_dll_info(pid):
    """Получить информацию о загруженных DLL в процессе"""
    try:
        process = psutil.Process(pid)
        dlls = []
        try:
            # Получаем список загруженных модулей (DLL)
            for module in process.memory_maps():
                if module.path and '.dll' in module.path.lower():
                    dlls.append(module.path)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            # Если не можем получить информацию о модулях, пробуем другой способ
            pass
        return dlls
    except Exception as e:
        return [f"Error getting DLL info: {str(e)}"]

def log_debug_info(interval=5):
    """Основной метод для логирования информации"""
    pid = get_pid()
    print(f"Process ID (PID): {pid}")
    
    while True:
        print("\n" + "="*60)
        print(f"DEBUG INFO - PID: {pid}")
        print("="*60)
        
        # Информация о потоках
        print("THREADS:")
        threads = get_thread_info()
        for thread in threads:
            print(f"  ID: {thread['id']}, Name: {thread['name']}, Daemon: {thread['daemon']}, Alive: {thread['is_alive']}")
        
        # Информация о памяти
        memory_info = get_memory_info(pid)
        print(f"\nMEMORY USAGE:")
        print(f"  RSS: {memory_info['rss'] / 1024 / 1024:.2f} MB")
        print(f"  VMS: {memory_info['vms'] / 1024 / 1024:.2f} MB")
        print(f"  Percent: {memory_info['percent']:.2f}%")
        
        # Информация о процессе
        process_info = get_process_info(pid)
        print(f"\nPROCESS INFO:")
        print(f"  CPU Percent: {process_info['cpu_percent']:.2f}%")
        print(f"  Number of Threads: {process_info['num_threads']}")
        print(f"  Open Files: {process_info['open_files']}")
        print(f"  Connections: {process_info['connections']}")
        
        # Обнаружение дебаггера
        debugger_detected = detect_debugger()
        print(f"\nDEBUGGER DETECTED: {'YES' if debugger_detected else 'NO'}")
        
        # Список DLL в процессе
        print(f"\nLOADED DLLS:")
        dlls = get_dll_info(pid)
        if dlls:
            for dll in dlls:  # Показываем первые 20 DLL
                print(f"  {dll}")
            if len(dlls) > 20:
                print(f"  ... and {len(dlls) - 20} more DLLs")
        else:
            print("  No DLLs found or error occurred")
        
        # Список модулей
        print(f"\nLOADED MODULES ({len(sys.modules)}):")
        modules = list(sys.modules.keys())[:20]  # Первые 20 модулей
        for module in modules:
            print(f"  {module}")
            
        # Список глобальных переменных
        print(f"\nGLOBAL VARIABLES:")
        globals_dict = globals()
        global_vars = list(globals_dict.keys())[:20]  # Первые 20 глобальных переменных
        for var in global_vars:
            print(f"  {var}")
            
        # Список локальных переменных функции
        print(f"\nLOCAL VARIABLES:")
        frame = sys._getframe(1)
        local_vars = list(frame.f_locals.keys())[:10]  # Первые 10 локальных переменных
        for var in local_vars:
            print(f"  {var}")
            
        # Список аргументов функции
        print(f"\nFUNCTION ARGUMENTS:")
        try:
            args = frame.f_code.co_varnames[:frame.f_code.co_argcount]
            for arg in args:
                print(f"  {arg}")
        except Exception as e:
            print(f"  Error getting arguments: {e}")
            
        # Список доступных функций
        print(f"\nAVAILABLE FUNCTIONS:")
        functions = [name for name, obj in globals().items() if callable(obj)]
        for func in functions[:10]:  # Первые 10 функций
            print(f"  {func}")
            
        # Список классов
        print(f"\nAVAILABLE CLASSES:")
        classes = [name for name, obj in globals().items() if isinstance(obj, type)]
        for cls in classes[:10]:  # Первые 10 классов
            print(f"  {cls}")
            
        # Список модулей, связанных с отладкой
        print(f"\nDEBUGGING MODULES:")
        debug_modules = [name for name in sys.modules.keys() if 'debug' in name.lower() or 'pdb' in name.lower()]
        for mod in debug_modules:
            print(f"  {mod}")
            
        # Список системных переменных
        print(f"\nSYSTEM VARIABLES:")
        system_vars = [name for name in globals().keys() if name.startswith('__')]
        for var in system_vars[:10]:  # Первые 10 системных переменных
            print(f"  {var}")
            
        # Список объектов в garbage collector
        print(f"\nGC OBJECTS:")
        objects = gc.get_objects()
        print(f"  Total objects: {len(objects)}")
        
        # Список активных потоков
        print(f"\nACTIVE THREADS:")
        active_threads = threading.active_count()
        print(f"  Active threads: {active_threads}")

        print("=" * 60)
        print("threads")
        for i in threading.enumerate():
            print(i)

        # Список потоков с их стеками
        print(f"\nTHREAD STACKS:")
        try:
            for thread_id, frame in sys._current_frames().items():
                print(f"  Thread ID: {thread_id}")
                print(f"    Frame: {frame}")

        except Exception as e:
            print(f"  Error getting thread stacks: {e}")

        print("\n" + "=" * 60)
        print("Next update in {} seconds...".format(interval))
        print("=" * 60)

        time.sleep(10)

# Запуск логгера
if __name__ == "__main__":
    try:
        log_debug_info(interval=5)
    except KeyboardInterrupt:
        print("\nLogger stopped by user.")