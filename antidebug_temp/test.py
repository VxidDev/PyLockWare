import psutil
import os
import sys
import threading
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DLLInjectionChecker:
    def __init__(self, check_interval=5, log_suspicious_only=True):
        """
        Инициализирует класс проверки инъекций DLL.

        :param check_interval: Интервал между проверками в секундах.
        :param log_suspicious_only: Логировать только подозрительные модули.
        """
        self.check_interval = check_interval
        self.log_suspicious_only = log_suspicious_only
        self.stop_event = threading.Event()
        self.thread = None
        self.injection_detected = False
        self.suspicious_modules_history = set()

        # Инициализация безопасных префиксов при создании экземпляра
        self.known_safe_prefixes = [
            os.environ.get('SYSTEMROOT', r'C:\Windows').lower(),
            os.environ.get('WINDIR', r'C:\Windows').lower(),
            sys.prefix.lower(),  # Директория установленного Python или venv
        ]
        # Добавляем директорию основного исполняемого файла Python (где лежат python3.dll и т.п.)
        # sys.base_prefix указывает на "корень" Python, например, C:\Users\fedor\AppData\Local\Programs\Python\Python312
        # Это важно, когда скрипт запущен из virtualenv.
        self.known_safe_prefixes.append(os.path.dirname(sys.executable).lower())  # Сначала директория exe (Scripts)
        self.known_safe_prefixes.append(sys.base_prefix.lower())  # Потом базовая директория Python (где DLLs)

    def get_current_process_loaded_modules(self):
        """Получает список путей к загруженным модулям текущего процесса."""
        try:
            current_pid = os.getpid()
            current_proc = psutil.Process(current_pid)
            loaded_dll_paths = set()
            for mmap in current_proc.memory_maps(grouped=False):
                if mmap.path:
                    loaded_dll_paths.add(mmap.path.lower())
            return sorted(list(loaded_dll_paths))
        except (psutil.AccessDenied, psutil.NoSuchProcess) as e:
            logger.error(f"Не удалось получить список модулей: {e}")
            return []

    def analyze_modules_for_injection(self, modules_list):
        """Анализирует список модулей на наличие потенциально инжектированных DLL."""
        suspicious_modules = []
        # Используем обновлённый список безопасных префиксов из __init__
        safe_prefixes = self.known_safe_prefixes

        for mod_path in modules_list:
            # Проверяем, начинается ли путь к модулю с одного из безопасных префиксов
            is_known_safe = any(
                mod_path.startswith(prefix) or
                # Дополнительно проверяем, находится ли файл в подкаталоге безопасного префикса
                # Это может быть полезно, если DLL находятся, например, в подпапке \DLLs
                any(os.path.commonpath([prefix, mod_path]) == prefix and mod_path.startswith(prefix) for prefix in
                    safe_prefixes)
                for prefix in safe_prefixes
            )

            if not is_known_safe and mod_path.endswith(('.dll', '.so', '.dylib')):
                if mod_path not in self.suspicious_modules_history:
                    self.suspicious_modules_history.add(mod_path)
                    suspicious_modules.append(mod_path)
                    logger.warning(f"Найден подозрительный модуль: {mod_path}")
                elif not self.log_suspicious_only:
                    logger.info(f"Подозрительный модуль (уже видели): {mod_path}")

        return suspicious_modules

    def run_check(self):
        """Цикл проверки, выполняемый в фоновом потоке."""
        while not self.stop_event.wait(timeout=self.check_interval):
            if self.injection_detected:
                # Если уже было обнаружено, можно остановить или продолжать
                # В этом варианте продолжаем проверять
                pass

            modules = self.get_current_process_loaded_modules()
            if not modules:
                logger.warning("Не удалось получить список модулей во время проверки.")
                continue

            suspicious = self.analyze_modules_for_injection(modules)

            if suspicious:
                self.injection_detected = True
                logger.critical("!!! СРАБОТАЛА СИСТЕМА САМОЗАЩИТЫ: возможна инъекция DLL. !!!")
                # Можно добавить дополнительную логику реакции здесь
                # Например, вызов callback'а, отправка сигнала, запись в файл и т.д.
                # self.on_injection_detected(suspicious)

    def start(self):
        """Запускает фоновую проверку."""
        if self.thread is not None and self.thread.is_alive():
            logger.warning("Фоновая проверка уже запущена.")
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self.run_check, daemon=True)
        self.thread.start()
        logger.info(f"Фоновая проверка инъекций DLL запущена (интервал: {self.check_interval} сек).")

    def stop(self):
        """Останавливает фоновую проверку."""
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join()
        logger.info("Фоновая проверка инъекций DLL остановлена.")

    def is_injected(self):
        """Возвращает True, если была обнаружена инъекция."""
        return self.injection_detected


# --- Пример использования ---
if __name__ == "__main__":
    print(os.getpid())
    checker = DLLInjectionChecker(check_interval=3, log_suspicious_only=True)

    try:
        checker.start()
        print("Скрипт работает. Проверка DLL запущена в фоне...")
        # Симуляция основной работы скрипта
        while True:
            time.sleep(1)
            # Можно периодически проверять статус
            # if checker.is_injected():
            #     print("Обнаружена инъекция! Принимаются меры...")
            #     break

    except KeyboardInterrupt:
        print("\nПолучен сигнал остановки.")
    finally:
        checker.stop()
        print("Программа завершена.")