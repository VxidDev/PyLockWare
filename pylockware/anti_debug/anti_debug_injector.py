#THIS IS A TEMPLATE

"""
Hardened anti-debug and anti-injection protection module
Based on test3.py from antidebug_temp
"""
import os
import sys
import platform
import threading
import time
import psutil
import win32api
import win32con
import win32process
import win32security


class HardenedInjectionDetector:
    """
    Усиленный детектор, который точно отличает инъекции от легитимных потоков.
    """

    def __init__(self):
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)

        # Собираем ВСЕ легитимные потоки при старте
        self.legitimate_threads = self._get_all_threads_snapshot()
        self.legitimate_python_threads = {th.ident for th in threading.enumerate() if th.ident}
        self.initial_modules = self._get_loaded_modules()

        # Для трекинга
        self.detected_injections = []
        self.last_alert_time = 0





    def _get_all_threads_snapshot(self):
        """Полный снимок всех потоков в процессе"""
        return {t.id for t in self.process.threads()}

    def is_definitely_remote_thread(self, thread_id):
        """
        Ключевая проверка: является ли поток RemoteThread (инъекцией)
        Методы, которые работают БЕЗ прав админа
        """
        suspicious_indicators = 0

        try:
            # 1. Проверяем через Windows API - НЕ открываем поток, просто проверяем
            try:
                # Пытаемся получить базовую информацию без полного доступа
                handle = win32api.OpenThread(
                    win32con.THREAD_QUERY_LIMITED_INFORMATION,  # Минимальные права
                    False,
                    thread_id
                )

                if handle:
                    # 2. Проверяем время создания потока
                    # У RemoteThread время создания обычно близко к текущему
                    creation_time = win32process.GetThreadTimes(handle)
                    handle.Close()

                    # Если время создания в пределах последних 5 секунд - подозрительно
                    current_time = time.time()
                    if hasattr(creation_time, 'CreationTime'):
                        thread_age = current_time - creation_time.CreationTime
                        if thread_age < 5.0:
                            suspicious_indicators += 2

            except Exception:
                # Если даже с LIMITED_INFORMATION не получается - очень подозрительно!
                suspicious_indicators += 3

            # 3. Проверка: поток НЕ в Python threading
            if thread_id not in self.legitimate_python_threads:
                suspicious_indicators += 2

            # 4. Проверка: поток НЕ был в исходном снимке
            if thread_id not in self.legitimate_threads:
                suspicious_indicators += 2

            # 5. Проверка CPU нагрузки (инжектированный код обычно пассивен сначала)
            thread_cpu_times = None
            for t in self.process.threads():
                if t.id == thread_id:
                    thread_cpu_times = t
                    break

            if thread_cpu_times:
                # Инжектированные потоки часто имеют 0 CPU time (ждут)
                if thread_cpu_times.user_time == 0 and thread_cpu_times.system_time == 0:
                    suspicious_indicators += 1
                # Но также проверим, если поток потребляет много CPU - тоже подозрительно
                elif (thread_cpu_times.user_time + thread_cpu_times.system_time) > 10.0:
                    suspicious_indicators += 1

            # 6. Проверяем, не крашится ли процесс после появления потока
            # (иногда инжекторы вызывают нестабильность)
            try:
                self.process.status()  # Простая проверка жив ли процесс
            except:
                suspicious_indicators += 5  # Процесс умер - очень подозрительно!

        except Exception as e:
            # Любая ошибка при анализе - подозрительно
            suspicious_indicators += 1

        return suspicious_indicators >= 5  # Порог увеличен

    def _get_loaded_modules(self):
        """Get list of currently loaded modules"""
        try:
            loaded_modules = set()
            for mmap in self.process.memory_maps():
                if mmap.path:
                    loaded_modules.add(mmap.path.lower())
            return loaded_modules
        except Exception:
            return set()

    def detect_injected_modules(self):
        """Detect injected DLLs/modules"""
        current_modules = self._get_loaded_modules()
        new_modules = current_modules - self.initial_modules

        # Known safe prefixes
        safe_prefixes = [
            os.environ.get('SYSTEMROOT', r'C:\Windows').lower(),
            sys.prefix.lower(),
            os.path.dirname(sys.executable).lower(),
            sys.base_prefix.lower()
        ]

        for module in new_modules:
            if module.endswith(('.dll', '.so', '.dylib')):
                is_safe = any(module.startswith(prefix) for prefix in safe_prefixes)
                if not is_safe:
                    # Check for known malicious patterns
                    suspicious_patterns = ['inject', 'hook', 'cheat', 'hack', 'shellcode', 'backdoor', 'trojan']
                    if any(pattern in module.lower() for pattern in suspicious_patterns):
                        return True, f"Suspicious module detected: {module}"
        return False, None

    def check_for_injections(self):
        """Проверяет новые потоки на инъекции"""
        try:
            current_threads = self._get_all_threads_snapshot()
            new_threads = current_threads - self.legitimate_threads

            for thread_id in new_threads:
                # Пропускаем, если это Python-поток
                if thread_id in self.legitimate_python_threads:
                    continue

                if self.is_definitely_remote_thread(thread_id):
                    self.detected_injections.append({
                        'thread_id': thread_id,
                        'timestamp': time.time(),
                        'type': 'remote_thread'
                    })
                    return True, f"Remote thread detected: {thread_id}"

            # Check for injected modules
            has_injected_module, module_reason = self.detect_injected_modules()
            if has_injected_module:
                return True, module_reason

            return False, None

        except Exception as e:
            # Если не можем проверить - тоже подозрительно
            return True, f"Cannot check threads: {str(e)}"

    def detect_debugger(self):
        """Detect if running under a debugger"""
        # Check for trace function (common in debuggers)
        if sys.gettrace() is not None:
            return True

        # Check for common debugger modules
        debugger_modules = {'pdb', 'pydevd', 'debugpy', 'pydev', 'pydevd_plugins'}
        for module in debugger_modules:
            if module in sys.modules:
                return True

        # Check for specific debugger environment variables
        if any(var for var in os.environ.keys() if 'DEBUG' in var.upper()):
            return True

        # Check for specific debugger-related globals
        if '__debugger__' in globals():
            return True

        # Check for interactive mode
        if hasattr(sys, 'ps1'):
            return True

        # Check for debugger-specific threads
        current_threads = threading.enumerate()
        debugger_thread_patterns = ['pydevd', 'debug', 'pdb']
        for thread in current_threads:
            thread_name = thread.name.lower()
            if any(pattern in thread_name for pattern in debugger_thread_patterns):
                return True

        return False

    def run_protection(self):
        """Main protection loop"""
        while True:
            try:
                # Check for debugger
                if self.detect_debugger():
                    self.trigger_protection("Debugger detected")
                    break

                # Check for injections
                has_injection, reason = self.check_for_injections()
                if has_injection:
                    self.trigger_protection(f"Injection detected: {reason}")
                    break

            except Exception:
                # If we can't check due to permissions, that's suspicious too
                self.trigger_protection("Protection mechanism compromised")
                break

            time.sleep(1)  # Check every second

    def trigger_protection(self, reason):
        """Trigger protection response"""
        # Hard crash without any console output
        while True:
            os._exit(1)

    def start_monitoring(self):
        """Start protection in a separate thread"""
        self.monitor_thread = threading.Thread(target=self.run_protection, daemon=True)
        self.monitor_thread.start()


# Global instance for easy access
protection_instance = None


def enable_protection():
    """Enable anti-debug/injection protection"""
    global protection_instance

    # Check if running on Windows AMD64
    if not (sys.platform == 'win32' and platform.machine().lower() in ['amd64', 'x86_64']):
        # Not running on Windows AMD64, skip protection
        return

    if protection_instance is None:
        protection_instance = HardenedInjectionDetector()
        protection_instance.start_monitoring()


def disable_protection():
    """Disable protection (for debugging purposes)"""
    global protection_instance
    if protection_instance:
        # Note: We can't easily stop the daemon thread, so we just let it run
        pass