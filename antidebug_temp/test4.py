import ctypes
import os
import sys
import threading
import time
from ctypes import wintypes
print(os.getpid())
if sys.maxsize > 2**32:
    ULONG_PTR = ctypes.c_ulonglong
else:
    ULONG_PTR = ctypes.c_ulong

def is_debugger_present() -> bool:
    return bool(ctypes.windll.kernel32.IsDebuggerPresent())


def check_remote_debugger_present() -> bool:
    kernel32 = ctypes.windll.kernel32
    is_debugged = wintypes.BOOL()

    result = kernel32.CheckRemoteDebuggerPresent(
        kernel32.GetCurrentProcess(),
        ctypes.byref(is_debugged)
    )

    if result == 0:
        return False

    return bool(is_debugged.value)


def peb_being_debugged() -> bool:
    kernel32 = ctypes.windll.kernel32
    ntdll = ctypes.windll.ntdll

    class PROCESS_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("Reserved1", wintypes.LPVOID),
            ("PebBaseAddress", wintypes.LPVOID),
            ("Reserved2", wintypes.LPVOID * 2),
            ("UniqueProcessId", ULONG_PTR),  # use our custom type
            ("Reserved3", wintypes.LPVOID),
        ]

    ProcessBasicInformation = 0
    pbi = PROCESS_BASIC_INFORMATION()

    status = ntdll.NtQueryInformationProcess(
        kernel32.GetCurrentProcess(),
        ProcessBasicInformation,
        ctypes.byref(pbi),
        ctypes.sizeof(pbi),
        None
    )

    if status != 0:
        return False

    peb_address = pbi.PebBaseAddress
    being_debugged = ctypes.c_ubyte.from_address(peb_address + 2).value

    return bool(being_debugged)


def debugger_detected() -> bool:
    return (
        is_debugger_present()
        or check_remote_debugger_present()
        or peb_being_debugged()
    )



def anti_debug_loop(interval: float = 2.0):
    while True:
        if debugger_detected():
            print("Debugger detected. Exiting.")
            # можно заменить на os._exit(1) при необходимости
            raise SystemExit(1)

        time.sleep(interval)


def start_anti_debug_thread():
    thread = threading.Thread(
        target=anti_debug_loop,
        daemon=True
    )
    thread.start()


# =========================
# Example usage
# =========================
if __name__ == "__main__":
    start_anti_debug_thread()

    # основной код программы
    while True:
        print("Program running...")
        time.sleep(5)