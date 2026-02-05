import psutil
import time
import os


class SimpleThreadMonitor:
    """Простой монитор подозрительных потоков"""

    def __init__(self):
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)
        self.initial_threads = {t.id for t in self.process.threads()}

    def check_for_new_threads(self):
        """Проверка на новые потоки"""
        current_threads = {t.id for t in self.process.threads()}
        new_threads = current_threads - self.initial_threads

        if new_threads:
            print(f"[ALERT] Обнаружены новые потоки: {new_threads}")
            return True
        return False

    def monitor(self, interval=1):
        """Бесконечный мониторинг"""
        print(f"Мониторинг потоков PID: {self.pid}")
        print(f"Начальные потоки: {self.initial_threads}")
        print("Нажмите Ctrl+C для остановки\n")

        while True:
            if self.check_for_new_threads():
                # Дополнительные проверки для новых потоков
                for thread in self.process.threads():
                    if thread.id not in self.initial_threads:
                        print(f"  Подозрительный поток ID: {thread.id}")
                        print(f"    CPU time: user={thread.user_time}, system={thread.system_time}")
            time.sleep(interval)


# Запуск
if __name__ == "__main__":
    monitor = SimpleThreadMonitor()
    monitor.monitor(interval=1)