import ctypes
import time
import os
import numpy as np
print(os.getpid())



dll = ctypes.CDLL(r"C:\Users\fedor\PycharmProjects\PyLockWare\native_src\PyLockWareRuntime\x64\Release\PyLockWareRuntime.dll")

dll.StartModuleMonitor()
time.sleep(1)

print("=" * 50)
print("1. Умножение больших матриц")
print("=" * 50)

# Создаем большие матрицы 5000x5000
size = 5000
A = np.random.rand(size, size)
B = np.random.rand(size, size)

start = time.time()
C = np.dot(A, B)  # или A @ B
end = time.time()
print(f"Умножение матриц {size}x{size}: {end - start:.2f} секунд")
print(f"Размер результата: {C.nbytes / 1024**3:.2f} ГБ")
print()


while True:
    time.sleep(2)

