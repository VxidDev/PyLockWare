import psutil
import time
import os
import sys
from datetime import datetime
import threading
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

        # Для трекинга
        self.detected_injections = []
        self.last_alert_time = 0

        print(f"[ХАРДЕНД-ДЕТЕКТОР] PID: {self.pid}")
        print(f"[ХАРДЕНД-ДЕТЕКТОР] Исходных потоков: {len(self.legitimate_threads)}")
        print(f"[ХАРДЕНД-ДЕТЕКТОР] Python-потоков: {len(self.legitimate_python_threads)}")
        print(f"[ХАРДЕНД-ДЕТЕКТОР] Ожидание инъекций...\n")

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
            for _ in range(3):  # Проверяем 3 раза
                for t in self.process.threads():
                    if t.id == thread_id:
                        # Инжектированные потоки часто имеют 0 CPU time (ждут)
                        if t.user_time == 0 and t.system_time == 0:
                            suspicious_indicators += 1
                        break
                time.sleep(0.01)

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

    def check_for_injections(self):
        """Проверяет новые потоки на инъекции"""
        try:
            current_threads = self._get_all_threads_snapshot()
            new_threads = current_threads - self.legitimate_threads

            for thread_id in new_threads:
                # Пропускаем, если это Python-поток
                if thread_id in self.legitimate_python_threads:
                    continue

                # Проверяем на RemoteThread
                if self.is_definitely_remote_thread(thread_id):
                    # ОБНАРУЖЕНА ИНЪЕКЦИЯ!
                    event = {
                        'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        'thread_id': thread_id,
                        'total_threads': len(current_threads),
                        'type': 'REMOTE_THREAD_INJECTION'
                    }

                    # Добавляем в список обнаруженных
                    self.detected_injections.append(event)

                    # Обновляем legitimate_threads, чтобы не детектить повторно
                    self.legitimate_threads.add(thread_id)

                    # Срочное оповещение
                    self.urgent_alert(event)

                    # Можно предпринять действия: завершить поток, завершить процесс и т.д.
                    # self.terminate_thread(thread_id)  # Осторожно!

                    return True

            # Обновляем список легитимных потоков (для потоков от C-расширений)
            self.legitimate_threads.update(new_threads)

            return False

        except Exception as e:
            print(f"[ОШИБКА] Ошибка проверки: {e}")
            return False

    def urgent_alert(self, event):
        """Экстренное оповещение об инъекции"""
        current_time = time.time()

        # Защита от спама алертами
        if current_time - self.last_alert_time < 2.0:
            return

        self.last_alert_time = current_time

        # Визуальное оповещение
        print("\n" + "🚨" * 30)
        print("🚨 КРИТИЧЕСКОЕ ОБНАРУЖЕНИЕ: ВНЕДРЕНИЕ КОДА 🚨")
        print("🚨" * 30)
        print(f"Время: {event['timestamp']}")
        print(f"Обнаружен RemoteThread: ID {event['thread_id']}")
        print(f"Всего потоков в процессе: {event['total_threads']}")
        print("Вероятность инъекции: ВЫСОКАЯ")
        print("🚨" * 30 + "\n")


        # Запись в лог файл
        self.log_to_file(event)

    def terminate_thread(self, thread_id):
        """Попытка завершить подозрительный поток (ОПАСНО!)"""
        try:
            handle = win32api.OpenThread(
                win32con.THREAD_TERMINATE,
                False,
                thread_id
            )
            if handle:
                win32api.TerminateThread(handle, 0)
                handle.Close()
                print(f"[ДЕЙСТВИЕ] Поток {thread_id} принудительно завершен!")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось завершить поток: {e}")

    def log_to_file(self, event):
        """Логирование в файл"""
        log_entry = (
            f"{event['timestamp']} | "
            f"INJECTION | "
            f"ThreadID:{event['thread_id']} | "
            f"Process:{self.process.name()}({self.pid})\n"
        )

        try:
            with open('injection_detection.log', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass

    def monitor(self, interval=0.5):
        """
        Основной цикл мониторинга.
        Интервал уменьшен для быстрого детекта.
        """
        print(f"[МОНИТОРИНГ] Начало с интервалом {interval} сек.")
        print("[МОНИТОРИНГ] Нажмите Ctrl+C для остановки\n")

        stats_counter = 0

        try:
            while True:
                # Основная проверка
                if self.check_for_injections():
                    # Если обнаружена инъекция, можно увеличить частоту проверок
                    interval = max(0.1, interval * 0.5)

                # Периодическая статистика
                stats_counter += 1
                if stats_counter >= 20:  # Каждые 20 проверок
                    current = len(self._get_all_threads_snapshot())
                    print(f"[СТАТ] Потоков: {current} | Обнаружено инъекций: {len(self.detected_injections)}")
                    stats_counter = 0

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n[МОНИТОРИНГ] Остановлен")
            self.print_final_report()

    def print_final_report(self):
        """Финальный отчет"""
        print("\n" + "=" * 60)
        print("ФИНАЛЬНЫЙ ОТЧЕТ ОБ ОБНАРУЖЕНИИ ИНЪЕКЦИЙ")
        print("=" * 60)

        if self.detected_injections:
            print(f"🚨 ОБНАРУЖЕНО ИНЪЕКЦИЙ: {len(self.detected_injections)} 🚨")
            for i, inj in enumerate(self.detected_injections, 1):
                print(f"\n{i}. Время: {inj['timestamp']}")
                print(f"   Thread ID: {inj['thread_id']}")
                print(f"   Тип: {inj['type']}")
        else:
            print("✓ Инъекций не обнаружено")

        current_threads = len(self._get_all_threads_snapshot())
        print(f"\nИтоговая статистика:")
        print(f"  Всего потоков: {current_threads}")
        print(f"  Python-потоков: {len(self.legitimate_python_threads)}")
        print(f"  Исходных потоков: {len(self.legitimate_threads)}")
        print("=" * 60)




# Основная программа
if __name__ == "__main__":
    print("=" * 60)
    print("HARDENED INJECTION DETECTOR v2.0")
    print("=" * 60)

    # Запуск теста при необходимости
    detector = HardenedInjectionDetector()

    detector.monitor(interval=0.0)




