"""
Native Anti-Debug Module for PyLockWare
Uses the native PyLockWareRuntime.dll for anti-debug and anti-injection protection
"""
import ctypes
import os
import sys
import platform
import threading
import time
import psutil
from pathlib import Path


class NativeAntiDebug:
    """
    Class that wraps the native PyLockWareRuntime.dll for anti-debug protection
    """

    def __init__(self):
        self.dll = None
        self.monitoring_thread = None
        self.running = False
        
        # Load the native DLL
        self.load_native_dll()

    def load_native_dll(self):
        """
        Load the PyLockWareRuntime.dll from the appropriate location
        """
        try:
            # Determine the path to the DLL
            # First, try to find it in the same directory as the current script
            current_dir = Path.cwd()  # Use current working directory (where the obfuscated app runs)
            dll_path = current_dir / "PyLockWareRuntime.dll"
            
            # If the DLL is not found in the current directory, try to find it relative to this file
            if not dll_path.exists():
                current_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
                dll_path = current_dir / "PyLockWareRuntime.dll"
                
            # If still not found, try the original location in the project
            if not dll_path.exists():
                dll_path = Path(__file__).parent / ".." / ".." / "native_src" / "PyLockWareRuntime" / "x64" / "Release" / "PyLockWareRuntime.dll"
                
            # If still not found, try to load it from the system path
            if not dll_path.exists():
                dll_path = "PyLockWareRuntime.dll"
            
            # Load the DLL
            if isinstance(dll_path, Path) and dll_path.exists():
                self.dll = ctypes.CDLL(str(dll_path))
            else:
                # If dll_path is a string or Path that doesn't exist, try to load directly
                # This might work if the DLL is in the system PATH
                self.dll = ctypes.CDLL(str(dll_path))
        except OSError as e:
            # Perform hard crash if DLL fails to load
            while True:
                os._exit(1)  # Immediate termination

    def start_module_monitor(self):
        """
        Call the StartModuleMonitor function from the native DLL
        """
        if self.dll:
            try:
                self.dll.StartModuleMonitor()
                return True
            except AttributeError:
                # StartModuleMonitor function not found in DLL - hard crash
                while True:
                    os._exit(1)  # Immediate termination
            except Exception as e:
                # Error calling StartModuleMonitor - hard crash
                while True:
                    os._exit(1)  # Immediate termination
        else:
            # DLL not loaded, cannot start module monitor - hard crash
            while True:
                os._exit(1)  # Immediate termination

    def run_protection(self):
        """
        Main protection loop - runs in a separate thread
        """
        # Start the native module monitor if DLL is available
        if self.dll:
            self.start_module_monitor()

        # Keep the protection running
        while self.running:
            try:
                # Check for debugger using Python methods
                if self.detect_debugger():
                    self.trigger_protection("Python-side debugger detected")
                    break

            except Exception:
                # If we can't check due to permissions, that's suspicious too
                self.trigger_protection("Protection mechanism compromised")
                break

            time.sleep(1)  # Sleep for 1 second before next check

    def trigger_protection(self, reason):
        """Trigger protection response"""
        # Hard crash without any console output
        while True:
            os._exit(1)

    def start_monitoring(self):
        """
        Start the protection in a separate thread
        """
        if self.dll is None:

            return

        self.running = True
        self.monitoring_thread = threading.Thread(target=self.run_protection, daemon=True)
        self.monitoring_thread.start()


    def stop_monitoring(self):
        """
        Stop the protection
        """
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish

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



# Global instance for easy access
protection_instance = None


def enable_protection():
    """
    Enable native anti-debug protection
    """
    global protection_instance

    # Check if running on Windows AMD64
    if not (sys.platform == 'win32' and platform.machine().lower() in ['amd64', 'x86_64']):
        # Not running on Windows AMD64, skip protection
        return

    if protection_instance is None:
        protection_instance = NativeAntiDebug()
        protection_instance.start_monitoring()


def disable_protection():
    """
    Disable protection (for debugging purposes)
    """
    global protection_instance
    if protection_instance:
        protection_instance.stop_monitoring()
        protection_instance = None