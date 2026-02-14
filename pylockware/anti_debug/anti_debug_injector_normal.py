"""
Normal anti-debug protection module
Based on the strict version but without thread checking
"""

import os
import sys
import platform
import threading
import time
import psutil


class NormalInjectionDetector:
    """
    Normal detector that provides basic anti-debug functionality without thread checking.
    """

    def __init__(self):
        self.pid = os.getpid()
        self.process = psutil.Process(self.pid)

        # Get initial loaded modules
        self.initial_modules = self._get_loaded_modules()

        # For tracking
        self.last_alert_time = 0

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

        # Antivirus and security software paths to whitelist
        antivirus_prefixes = [
            r'C:\Program Files\Windows Defender',
            r'C:\Program Files\AVAST Software',
            r'C:\Program Files\AVG',
            r'C:\Program Files\Malwarebytes',
            r'C:\Program Files\ESET',
            r'C:\Program Files\Bitdefender',
            r'C:\Program Files\Kaspersky Lab',
            r'C:\Program Files\Symantec',
            r'C:\Program Files\Trend Micro',
            r'C:\Program Files\McAfee',
            r'C:\Program Files\Norton',
            r'C:\Program Files\Panda Security',
            r'C:\Program Files\Sophos',
            r'C:\Program Files\Comodo',
            r'C:\Program Files\F-Secure',
            r'C:\Program Files\ZoneAlarm',
            r'C:\Program Files\Ad-Aware',
            r'C:\Program Files\Webroot',
            r'C:\Program Files\Emsisoft'
        ]

        for module in new_modules:
            if module.endswith(('.dll', '.so', '.dylib')):
                # Check if it's from a safe location
                is_safe = any(module.startswith(prefix.lower()) for prefix in safe_prefixes)
                
                # Check if it's from an antivirus/security software location
                is_antivirus = any(module.startswith(prefix.lower()) for prefix in antivirus_prefixes)
                
                if not is_safe and not is_antivirus:
                    # Check for known malicious patterns
                    suspicious_patterns = ['inject', 'hook', 'cheat', 'hack', 'shellcode', 'backdoor', 'trojan', 'keygen', 'crack', 'loader', 'x64dbg', 'ollydbg', 'ida', 'ghidra', 'scyllahide', 'membly', 'Extreme Injector', 'Cheat Engine', 'Process Hacker', 'Autoruns', 'Procmon', 'Wireshark', 'Fiddler', 'Burp Suite', 'Metasploit', 'Nmap', 'Hydra', 'John the Ripper', 'Hashcat', 'sqlmap', 'nikto', 'dirb', 'gobuster', 'wfuzz', 'pyinject', 'pyshell']
                    if any(pattern in module.lower() for pattern in suspicious_patterns):
                        return True, f"Suspicious module detected: {module}"
        return False, None

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

                # Check for injected modules
                has_injected_module, module_reason = self.detect_injected_modules()
                if has_injected_module:
                    self.trigger_protection(f"Injection detected: {module_reason}")
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
    """Enable anti-debug protection"""
    global protection_instance

    # Check if running on Windows AMD64
    if not (sys.platform == 'win32' and platform.machine().lower() in ['amd64', 'x86_64']):
        # Not running on Windows AMD64, skip protection
        return

    if protection_instance is None:
        protection_instance = NormalInjectionDetector()
        protection_instance.start_monitoring()


def disable_protection():
    """Disable protection (for debugging purposes)"""
    global protection_instance
    if protection_instance:
        # Note: We can't easily stop the daemon thread, so we just let it run
        pass