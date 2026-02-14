#include "pch.h"
#include <intrin.h>

static HANDLE g_thread = NULL;
static volatile BOOL g_running = FALSE;
static HMODULE g_hModule = NULL;
static LPVOID g_exeBase = NULL;
static DWORD g_mainThreadId = 0;

// Тип функции NtQueryInformationThread
typedef NTSTATUS(WINAPI* pNtQueryInformationThread)(
    HANDLE ThreadHandle,
    ULONG ThreadInformationClass,
    PVOID ThreadInformation,
    ULONG ThreadInformationLength,
    PULONG ReturnLength
    );

// Тип функции NtQueryInformationProcess
typedef NTSTATUS(WINAPI* pNtQueryInformationProcess)(
    HANDLE ProcessHandle,
    ULONG ProcessInformationClass,
    PVOID ProcessInformation,
    ULONG ProcessInformationLength,
    PULONG ReturnLength
    );

static pNtQueryInformationThread g_NtQueryInformationThread = nullptr;
static pNtQueryInformationProcess g_NtQueryInformationProcess = nullptr;

// Структура для белого списка
struct KnownModule {
    std::string name;
    std::string fullPath;
    LPVOID base;
    bool isExe;
    bool isTrusted;
};

std::vector<KnownModule> g_knownModules;

// Список доверенных издателей/модулей
struct TrustedModule {
    const char* namePattern;
    const char* pathPattern;
    bool isSystem;
};

std::vector<TrustedModule> g_trustedPatterns = {
    {"ntdll.dll", nullptr, true},
    {"kernel32.dll", nullptr, true},
    {"kernelbase.dll", nullptr, true},
    {"user32.dll", nullptr, true},
    {"gdi32.dll", nullptr, true},
    {"win32u.dll", nullptr, true},
    {"msvcrt.dll", nullptr, true},
    {"ucrtbase.dll", nullptr, true},
    {"advapi32.dll", nullptr, true},
    {"shell32.dll", nullptr, true},
    {"ole32.dll", nullptr, true},
    {"oleaut32.dll", nullptr, true},
    {"combase.dll", nullptr, true},
    {"rpcrt4.dll", nullptr, true},
    {"ws2_32.dll", nullptr, true},
    {"sechost.dll", nullptr, true},
    {"bcrypt.dll", nullptr, true},
    {"crypt32.dll", nullptr, true},
    {"python3.dll", nullptr, false},
    {"python39.dll", nullptr, false},
    {"python310.dll", nullptr, false},
    {"python311.dll", nullptr, false},
    {"python312.dll", nullptr, false},
    {"python313.dll", nullptr, false},
    {"windhawk.dll", "windhawk", false},
    {"pytransform.dll", nullptr, false},
    {"vcruntime140.dll", nullptr, false},
    {"vcruntime140_1.dll", nullptr, false},
    {"msvcp140.dll", nullptr, false},
    {"concrt140.dll", nullptr, false},
    { "_ctypes.pyd", nullptr, false },
    {"_socket.pyd", nullptr, false},
    {"_ssl.pyd", nullptr, false},
    {"_hashlib.pyd", nullptr, false},
    {"_asyncio.pyd", nullptr, false},
    {"_multiprocessing.pyd", nullptr, false},
    {"_queue.pyd", nullptr, false},
    {"_uuid.pyd", nullptr, false},
    {"_zoneinfo.pyd", nullptr, false},
    {"_decimal.pyd", nullptr, false},
    {"_elementtree.pyd", nullptr, false},
    {"_bz2.pyd", nullptr, false},
    {"_lzma.pyd", nullptr, false},
    {"pyexpat.pyd", nullptr, false},
    {"select.pyd", nullptr, false},
    {"unicodedata.pyd", nullptr, false},
    {"winsound.pyd", nullptr, false},
    {"libffi-8.dll", nullptr, false},
    {"vcruntime140.dll", nullptr, false},
    {"vcruntime140_1.dll", nullptr, false},
    {"msvcp140.dll", nullptr, false},
    {"msvcp140_1.dll", nullptr, false},
    {"msvcp140_2.dll", nullptr, false},
    {"concrt140.dll", nullptr, false},
    {"PyLockWareRuntime.dll", nullptr, false}
};

// Используем системные структуры из winternl.h или определяем только если нужно
// PEB и PROCESS_BASIC_INFORMATION уже определены в Windows SDK

// Преобразование широкой строки в многобайтовую
std::string WCharToString(const WCHAR* wstr)
{
    if (!wstr) return std::string();
    int size_needed = WideCharToMultiByte(CP_UTF8, 0, wstr, -1, NULL, 0, NULL, NULL);
    std::string strTo(size_needed, 0);
    WideCharToMultiByte(CP_UTF8, 0, wstr, -1, &strTo[0], size_needed, NULL, NULL);
    if (!strTo.empty() && strTo.back() == '\0') {
        strTo.pop_back();
    }
    return strTo;
}

bool IsPathInTrustedList(const char* fullPath, const char* moduleName)
{
    if (!fullPath) return false;
    std::string pathLower = fullPath;
    std::string nameLower = moduleName ? moduleName : "";
    std::transform(pathLower.begin(), pathLower.end(), pathLower.begin(), ::tolower);
    std::transform(nameLower.begin(), nameLower.end(), nameLower.begin(), ::tolower);

    for (const auto& trusted : g_trustedPatterns) {
        if (trusted.namePattern) {
            std::string patternLower = trusted.namePattern;
            std::transform(patternLower.begin(), patternLower.end(), patternLower.begin(), ::tolower);
            if (nameLower.find(patternLower) != std::string::npos) return true;
        }
        if (trusted.pathPattern) {
            std::string pathPatternLower = trusted.pathPattern;
            std::transform(pathPatternLower.begin(), pathPatternLower.end(), pathPatternLower.begin(), ::tolower);
            if (pathLower.find(pathPatternLower) != std::string::npos) return true;
        }
        if (trusted.isSystem) {
            if (pathLower.find("\\system32\\") != std::string::npos ||
                pathLower.find("\\syswow64\\") != std::string::npos) return true;
        }
    }
    if (pathLower.find("\\numpy") != std::string::npos ||
        pathLower.find("\\python") != std::string::npos)
    {
        return true;
    }
    return false;
}

void InitKnownModules()
{
    g_knownModules.clear();
    MEMORY_BASIC_INFORMATION mbi;
    if (VirtualQuery((LPVOID)GetModuleHandleA(NULL), &mbi, sizeof(mbi))) {
        g_exeBase = mbi.AllocationBase;
        char exePath[MAX_PATH];
        GetModuleFileNameA(NULL, exePath, MAX_PATH);
        char* exeName = strrchr(exePath, '\\');
        if (exeName) exeName++; else exeName = exePath;
        KnownModule entry = {
            std::string(exeName),
            std::string(exePath),
            g_exeBase,
            true,
            true
        };
        g_knownModules.push_back(entry);
    }

    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, GetCurrentProcessId());
    if (hSnapshot != INVALID_HANDLE_VALUE) {
        MODULEENTRY32W me;
        me.dwSize = sizeof(me);
        if (Module32FirstW(hSnapshot, &me)) {
            do {
                if (me.modBaseAddr == g_exeBase) continue;
                bool found = false;
                for (const auto& mod : g_knownModules) {
                    if (mod.base == me.modBaseAddr) {
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    std::string moduleName = WCharToString(me.szModule);
                    std::string modulePath = WCharToString(me.szExePath);
                    bool isTrusted = IsPathInTrustedList(modulePath.c_str(), moduleName.c_str());
                    KnownModule entry = {
                        moduleName,
                        modulePath,
                        me.modBaseAddr,
                        false,
                        isTrusted
                    };
                    g_knownModules.push_back(entry);
                }
            } while (Module32NextW(hSnapshot, &me));
        }
        CloseHandle(hSnapshot);
    }
}

bool IsAddressInKnownModule(LPVOID address)
{
    MEMORY_BASIC_INFORMATION mbi;
    if (!VirtualQuery(address, &mbi, sizeof(mbi)))
        return false;
    LPVOID moduleBase = mbi.AllocationBase;
    if (!moduleBase)
        return false;
    for (const auto& module : g_knownModules) {
        if (module.base == moduleBase) {
            return true;
        }
    }
    return false;
}

bool IsAddressTrusted(LPVOID address)
{
    MEMORY_BASIC_INFORMATION mbi;
    if (!VirtualQuery(address, &mbi, sizeof(mbi)))
        return false;
    LPVOID moduleBase = mbi.AllocationBase;
    if (!moduleBase)
        return false;
    for (const auto& module : g_knownModules) {
        if (module.base == moduleBase) {
            return module.isTrusted;
        }
    }
    return false;
}

bool IsMainThread(DWORD threadId)
{
    return threadId == g_mainThreadId;
}

void EnableMitigations()
{
    PROCESS_MITIGATION_IMAGE_LOAD_POLICY img = {};
    img.NoRemoteImages = 1;
    img.NoLowMandatoryLabelImages = 1;
    SetProcessMitigationPolicy(ProcessImageLoadPolicy, &img, sizeof(img));
}

// Функция для мгновенного краша процесса
void CrashProcess()
{
    TerminateProcess(GetCurrentProcess(), 1);
    __fastfail(FAST_FAIL_FATAL_APP_EXIT);
    *((volatile int*)nullptr) = 0;
    ExitProcess(0xDEAD);
}

// ==================== НОВЫЕ ПРОВЕРКИ ОТЛАДЧИКА ====================

// 1. Проверка IsDebuggerPresent
bool IsDebuggerPresentCheck()
{
    return IsDebuggerPresent() != FALSE;
}

// 2. Проверка CheckRemoteDebuggerPresent
bool CheckRemoteDebuggerPresentCheck()
{
    BOOL isDebugged = FALSE;
    typedef BOOL(WINAPI* pCheckRemoteDebuggerPresent)(HANDLE, PBOOL);

    HMODULE hKernel32 = GetModuleHandleA("kernel32.dll");
    if (!hKernel32) return false;

    pCheckRemoteDebuggerPresent pFunc = (pCheckRemoteDebuggerPresent)
        GetProcAddress(hKernel32, "CheckRemoteDebuggerPresent");

    if (!pFunc) return false;

    if (!pFunc(GetCurrentProcess(), &isDebugged))
        return false;

    return isDebugged != FALSE;
}

// 3. Проверка PEB.BeingDebugged через NtQueryInformationProcess
bool PEBBeingDebuggedCheck()
{
    if (!g_NtQueryInformationProcess)
        return false;

    // Используем системную структуру PROCESS_BASIC_INFORMATION
    // Определяем её вручную для совместимости
    typedef struct _MY_PROCESS_BASIC_INFORMATION {
        PVOID Reserved1;
        PVOID PebBaseAddress;
        PVOID Reserved2[2];
        ULONG_PTR UniqueProcessId;
        PVOID Reserved3;
    } MY_PROCESS_BASIC_INFORMATION;

    typedef struct _MY_PEB {
        BYTE Reserved1[2];
        BYTE BeingDebugged;
        BYTE Reserved2[1];
        PVOID Reserved3[2];
        PVOID Ldr;
        PVOID ProcessParameters;
        PVOID Reserved4[3];
        PVOID AtlThunkSListPtr;
        PVOID Reserved5;
        ULONG Reserved6;
        PVOID Reserved7;
        ULONG Reserved8;
        ULONG AtlThunkSListPtr32;
        PVOID Reserved9[45];
        BYTE Reserved10[96];
        PVOID PostProcessInitRoutine;
        BYTE Reserved11[128];
        PVOID Reserved12[1];
        ULONG SessionId;
    } MY_PEB, * PMY_PEB;

    MY_PROCESS_BASIC_INFORMATION pbi = {};
    ULONG returnLength = 0;

    NTSTATUS status = g_NtQueryInformationProcess(
        GetCurrentProcess(),
        0, // ProcessBasicInformation
        &pbi,
        sizeof(pbi),
        &returnLength
    );

    if (status != 0)
        return false;

    if (!pbi.PebBaseAddress)
        return false;

    // BeingDebugged находится по смещению 0x2 в PEB
    PMY_PEB peb = (PMY_PEB)pbi.PebBaseAddress;
    return peb->BeingDebugged != 0;
}

// 4. Проверка через Debug registers (аппаратные точки останова)
bool CheckHardwareBreakpoints()
{
    CONTEXT ctx = {};
    ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;

    if (!GetThreadContext(GetCurrentThread(), &ctx))
        return false;

    // Проверяем DR0-DR3 (адреса точек останова)
    // Если любой из них не ноль, значит установлена hardware breakpoint
    if (ctx.Dr0 || ctx.Dr1 || ctx.Dr2 || ctx.Dr3)
        return true;

    return false;
}

// 5. Проверка на наличие отладочного порта через NtQueryInformationProcess
bool CheckDebugPort()
{
    if (!g_NtQueryInformationProcess)
        return false;

    DWORD_PTR debugPort = 0;  // Используем DWORD_PTR для x64 совместимости
    ULONG returnLength = 0;

    // ProcessDebugPort = 7
    NTSTATUS status = g_NtQueryInformationProcess(
        GetCurrentProcess(),
        7, // ProcessDebugPort
        &debugPort,
        sizeof(debugPort),
        &returnLength
    );

    if (status != 0)
        return false;

    return debugPort != 0;
}

// 6. Проверка ProcessDebugFlags
bool CheckProcessDebugFlags()
{
    if (!g_NtQueryInformationProcess)
        return false;

    DWORD debugFlags = 0;
    ULONG returnLength = 0;

    // ProcessDebugFlags = 0x1F
    NTSTATUS status = g_NtQueryInformationProcess(
        GetCurrentProcess(),
        0x1F, // ProcessDebugFlags
        &debugFlags,
        sizeof(debugFlags),
        &returnLength
    );

    if (status != 0)
        return false;

    // Если флаг 0, значит процесс отлаживается
    return debugFlags == 0;
}

// 7. Проверка через NtGlobalFlag в PEB
bool CheckNtGlobalFlag()
{
    if (!g_NtQueryInformationProcess)
        return false;

    typedef struct _MY_PROCESS_BASIC_INFORMATION {
        PVOID Reserved1;
        PVOID PebBaseAddress;
        PVOID Reserved2[2];
        ULONG_PTR UniqueProcessId;
        PVOID Reserved3;
    } MY_PROCESS_BASIC_INFORMATION;

    MY_PROCESS_BASIC_INFORMATION pbi = {};
    ULONG returnLength = 0;

    NTSTATUS status = g_NtQueryInformationProcess(
        GetCurrentProcess(),
        0, // ProcessBasicInformation
        &pbi,
        sizeof(pbi),
        &returnLength
    );

    if (status != 0 || !pbi.PebBaseAddress)
        return false;

    // NtGlobalFlag находится по смещению 0xBC (x64) или 0x68 (x86)
    DWORD ntGlobalFlag = 0;
#ifdef _WIN64
    ntGlobalFlag = *(DWORD*)((BYTE*)pbi.PebBaseAddress + 0xBC);
#else
    ntGlobalFlag = *(DWORD*)((BYTE*)pbi.PebBaseAddress + 0x68);
#endif

    // Проверяем флаги FLG_HEAP_ENABLE_TAIL_CHECK (0x10), 
    // FLG_HEAP_ENABLE_FREE_CHECK (0x20), FLG_HEAP_VALIDATE_PARAMETERS (0x40)
    const DWORD DEBUG_FLAGS = 0x70; // 0x10 | 0x20 | 0x40
    return (ntGlobalFlag & DEBUG_FLAGS) != 0;
}

// 8. Проверка на наличие отладочной строки в PEB (ProcessHeap)
bool CheckProcessHeapFlags()
{
    if (!g_NtQueryInformationProcess)
        return false;

    typedef struct _MY_PROCESS_BASIC_INFORMATION {
        PVOID Reserved1;
        PVOID PebBaseAddress;
        PVOID Reserved2[2];
        ULONG_PTR UniqueProcessId;
        PVOID Reserved3;
    } MY_PROCESS_BASIC_INFORMATION;

    MY_PROCESS_BASIC_INFORMATION pbi = {};
    ULONG returnLength = 0;

    NTSTATUS status = g_NtQueryInformationProcess(
        GetCurrentProcess(),
        0, // ProcessBasicInformation
        &pbi,
        sizeof(pbi),
        &returnLength
    );

    if (status != 0 || !pbi.PebBaseAddress)
        return false;

    // Получаем ProcessHeap из PEB (смещение 0x30 x64, 0x18 x86)
    PVOID processHeap = nullptr;
    DWORD heapFlags = 0;
    DWORD heapForceFlags = 0;

#ifdef _WIN64
    processHeap = *(PVOID*)((BYTE*)pbi.PebBaseAddress + 0x30);
    if (processHeap) {
        // Флаги кучи находятся по смещению 0x70 и 0x74 в структуре кучи
        heapFlags = *(DWORD*)((BYTE*)processHeap + 0x70);
        heapForceFlags = *(DWORD*)((BYTE*)processHeap + 0x74);
    }
#else
    processHeap = *(PVOID*)((BYTE*)pbi.PebBaseAddress + 0x18);
    if (processHeap) {
        heapFlags = *(DWORD*)((BYTE*)processHeap + 0x40);
        heapForceFlags = *(DWORD*)((BYTE*)processHeap + 0x44);
    }
#endif

    if (heapForceFlags != 0)
        return true;

    // При отладке обычно устанавливаются флаги HEAP_TAIL_CHECKING_ENABLED (0x20)
    // и HEAP_FREE_CHECKING_ENABLED (0x40)
    const DWORD DEBUG_HEAP_FLAGS = 0x60; // 0x20 | 0x40
    return (heapFlags & DEBUG_HEAP_FLAGS) != 0;
}

// 9. Проверка через TLS callback (анти-отладка на старте) - исключения
bool CheckDebuggerViaCloseHandle()
{
    // Попытка закрыть невалидный handle с защитой SEH
    __try {
        // Используем правильное приведение типов для HANDLE
        CloseHandle((HANDLE)(ULONG_PTR)0xDEADBEEF);
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        // Если сработало исключение, отладчик может перехватить его
        // В нормальном режиме должно быть STATUS_INVALID_HANDLE
        return false;
    }
    return false;
}

// 10. Проверка времени выполнения (тайминг-атака)
bool CheckTimingAttack()
{
    LARGE_INTEGER freq, start, end;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&start);

    // Выполняем простую операцию
    volatile int dummy = 0;
    for (int i = 0; i < 1000; i++) {
        dummy += i;
    }

    QueryPerformanceCounter(&end);

    double elapsedMs = (double)(end.QuadPart - start.QuadPart) * 1000.0 / freq.QuadPart;

    // Если выполнение заняло слишком много времени (более 100мс для 1000 итераций),
    // возможно, выполнение было приостановлено отладчиком
    return elapsedMs > 100.0;
}

// Общая функция проверки всех методов
bool DebuggerDetected()
{
    return IsDebuggerPresentCheck() ||
        CheckRemoteDebuggerPresentCheck() ||
        PEBBeingDebuggedCheck() ||
        CheckHardwareBreakpoints() ||
        CheckDebugPort() ||
        CheckProcessDebugFlags() ||
        CheckNtGlobalFlag() ||
        CheckProcessHeapFlags() ||
        CheckDebuggerViaCloseHandle() ||
        CheckTimingAttack();
}

// ==================== КОНЕЦ НОВЫХ ПРОВЕРОК ====================

void DetectSuspiciousThreads()
{
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return;

    THREADENTRY32 te;
    te.dwSize = sizeof(te);
    DWORD currentPID = GetCurrentProcessId();

    if (Thread32First(snapshot, &te))
    {
        do {
            if (te.th32OwnerProcessID == currentPID)
            {
                if (IsMainThread(te.th32ThreadID))
                    continue;

                HANDLE hThread = OpenThread(THREAD_QUERY_INFORMATION, FALSE, te.th32ThreadID);
                if (hThread)
                {
                    LPVOID startAddr = nullptr;
                    if (g_NtQueryInformationThread)
                    {
                        NTSTATUS status = g_NtQueryInformationThread(
                            hThread,
                            9, // ThreadQuerySetWin32StartAddress
                            &startAddr,
                            sizeof(startAddr),
                            nullptr
                        );

                        if (status == 0 && startAddr != nullptr)
                        {
                            if (!IsAddressTrusted(startAddr))
                            {
                                MEMORY_BASIC_INFORMATION mbi;
                                if (VirtualQuery(startAddr, &mbi, sizeof(mbi)))
                                {
                                    char modulePath[MAX_PATH] = "unknown";
                                    HMODULE hMod = (HMODULE)mbi.AllocationBase;
                                    GetModuleFileNameA(hMod, modulePath, MAX_PATH);

                                    std::string modulePathStr(modulePath);
                                    std::transform(modulePathStr.begin(), modulePathStr.end(),
                                        modulePathStr.begin(), ::tolower);

                                    // Игнорируем легитимные вычислительные потоки
                                    if (modulePathStr.find("openblas") != std::string::npos ||
                                        modulePathStr.find("mkl") != std::string::npos ||
                                        modulePathStr.find("tbb") != std::string::npos ||
                                        modulePathStr.find("blas") != std::string::npos)
                                    {
                                        CloseHandle(hThread);
                                        continue;
                                    }

                                    // КРАШ ПРОЦЕССА
                                    CrashProcess();
                                }
                            }
                        }
                    }
                    CloseHandle(hThread);
                }
            }
        } while (Thread32Next(snapshot, &te));
    }

    CloseHandle(snapshot);
}

// Мониторингный поток
DWORD WINAPI MonitorThread(LPVOID lpParam)
{
    g_mainThreadId = GetCurrentThreadId();
    Sleep(10);
    InitKnownModules();

    int checkCount = 0;
    while (g_running)
    {
        // Проверка подозрительных потоков
        DetectSuspiciousThreads();

        // Проверка отладчика (каждый цикл)
        if (DebuggerDetected())
        {
            CrashProcess();
        }

        checkCount++;
        if (checkCount % 15 == 0) {
            InitKnownModules();
        }

        Sleep(2000); // Интервал 2 секунды как в test4.py
    }
    return 0;
}

// Экспортируемая функция для добавления модуля в белый список
extern "C" __declspec(dllexport)
void AddToWhitelist(const char* moduleName)
{
    // Исправление C6387: проверяем moduleName на NULL
    if (!moduleName) return;

    HMODULE hMod = GetModuleHandleA(moduleName);
    if (hMod) {
        for (auto& mod : g_knownModules) {
            if (mod.base == hMod) {
                if (!mod.isTrusted) {
                    mod.isTrusted = true;
                }
                return;
            }
        }
        char fullPath[MAX_PATH] = { 0 };
        GetModuleFileNameA(hMod, fullPath, MAX_PATH);
        KnownModule entry = {
            std::string(moduleName),
            std::string(fullPath),
            hMod,
            false,
            true
        };
        g_knownModules.push_back(entry);
    }
}

// Экспортируемая функция
extern "C" __declspec(dllexport)
void StartModuleMonitor()
{
    g_hModule = GetModuleHandleA("PyLockWareRuntime.dll");
    if (g_hModule == NULL)
    {
        g_hModule = GetModuleHandleA(NULL);
    }

    EnableMitigations();

    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (hNtdll)
    {
        g_NtQueryInformationThread = (pNtQueryInformationThread)
            GetProcAddress(hNtdll, "NtQueryInformationThread");

        g_NtQueryInformationProcess = (pNtQueryInformationProcess)
            GetProcAddress(hNtdll, "NtQueryInformationProcess");
    }

    if (g_thread != NULL)
        return;

    printf("Protected by PyLockWare runtime protection\n");
    g_running = TRUE;
    g_thread = CreateThread(NULL, 0, MonitorThread, NULL, 0, NULL);
}

// DllMain
BOOL APIENTRY DllMain(HMODULE hModule,
    DWORD  ul_reason_for_call,
    LPVOID lpReserved
)
{
    switch (ul_reason_for_call)
    {
    case DLL_PROCESS_ATTACH:
        g_hModule = hModule;
        DisableThreadLibraryCalls(hModule);
        break;

    case DLL_PROCESS_DETACH:
        g_running = FALSE;
        if (g_thread)
        {
            WaitForSingleObject(g_thread, 3000);
            CloseHandle(g_thread);
            g_thread = NULL;
        }
        break;
    }
    return TRUE;
}