#!/usr/bin/env python3
"""
PyLockWare CLI Entry Point
Command-line interface for the Python obfuscation suite
"""

import argparse
import sys
from pathlib import Path

# Add the project root to the path so we can import pylockware
sys.path.insert(0, str(Path(__file__).parent))

from pylockware.core.obfuscator import PyObfuscator


def main():
    parser = argparse.ArgumentParser(description="PyLockWare - Python Obfuscation Suite")
    parser.add_argument("project_path", help="Path to the project to obfuscate")
    parser.add_argument("--entry-point", required=True, help="Entry point file of the project (e.g., main.py)")
    parser.add_argument("--entry-function", default="main", help="Main function name in the entry point (default: main)")
    parser.add_argument("--banner", default="Obfuscated by PyLockWare Obfuscator", help="Banner text to add to modules")
    parser.add_argument("--output-dir", default="dist", help="Output directory for obfuscated project (default: dist)")
    parser.add_argument("--remap", action="store_true", help="Enable renaming of functions, variables, etc. to random names")
    parser.add_argument("--anti-debug", choices=['normal', 'strict', 'native'], help="Enable anti-debug and anti-injection protection ('normal' without thread checking, 'strict' with thread checking, 'native' for native implementation)")
    parser.add_argument("--string-prot", action="store_true", help="Enable string protection using base64 and zlib encoding")
    parser.add_argument("--num-obf", action="store_true", help="Enable number obfuscation using arithmetic expressions")
    parser.add_argument("--import-obf", action="store_true", help="Enable import obfuscation using dynamic execution techniques")
    parser.add_argument("--state-machine", action="store_true", help="Enable state machine obfuscation to transform functions into state machines")
    parser.add_argument("--builtin-dispatcher", action="store_true", help="Enable builtin dispatcher obfuscation to replace built-in calls with dispatcher calls")
    parser.add_argument("--name-gen", choices=['english', 'chinese', 'mixed', 'numbers', 'hex'],
                       default='english', help="Character set for name generation (default: english)")

    # Nuitka EXE packaging options
    nuitka_group = parser.add_argument_group("Nuitka EXE Packaging Options")
    nuitka_group.add_argument("--nuitka", action="store_true", help="Enable packaging into EXE using Nuitka")
    nuitka_group.add_argument("--nuitka-onefile", action="store_true", default=True, help="Create a single executable file with --onefile (default: True)")
    nuitka_group.add_argument("--nuitka-no-onefile", action="store_false", dest="nuitka_onefile", help="Disable --onefile option")
    nuitka_group.add_argument("--nuitka-standalone", action="store_true", default=True, help="Create a standalone distribution with --standalone (default: True)")
    nuitka_group.add_argument("--nuitka-no-standalone", action="store_false", dest="nuitka_standalone", help="Disable --standalone option")
    nuitka_group.add_argument("--nuitka-output-name", type=str, help="Custom name for the output executable")
    nuitka_group.add_argument("--nuitka-disable-console", action="store_true", default=True, help="Disable console window for GUI applications (Windows only, default: True)")
    nuitka_group.add_argument("--nuitka-enable-console", action="store_false", dest="nuitka_disable_console", help="Enable console window")
    nuitka_group.add_argument("--nuitka-icon", type=str, help="Path to .ico file for the executable icon (Windows only)")
    nuitka_group.add_argument("--nuitka-admin", action="store_true", help="Request administrator privileges (Windows UAC)")
    nuitka_group.add_argument("--nuitka-plugins", type=str, nargs='+', help="List of Nuitka plugins to enable (e.g., tk-inter, pyside6, numpy, multiprocessing)")
    nuitka_group.add_argument("--nuitka-extra-imports", type=str, nargs='+', help="List of additional modules to include explicitly")
    nuitka_group.add_argument("--nuitka-options", type=str, nargs='+', help="Additional custom Nuitka command-line options")

    args = parser.parse_args()

    # Check if anti-debug is requested but platform is not Windows AMD64
    import platform
    import sys
    if args.anti_debug and not (sys.platform == 'win32' and platform.machine().lower() in ['amd64', 'x86_64']):
        print("Warning: Anti-debug protection is only available for Windows AMD64. Option will be ignored.")
        args.anti_debug = None

    # Warn about incompatible options with Nuitka
    if args.nuitka:
        if args.anti_debug:
            print("\n" + "="*70)
            print("WARNING: Anti-debug is incompatible with Nuitka EXE packaging.")
            print("         Anti-debug has been disabled.")
            print("         For production protection, use protectors like Themida/VMProtect")
            print("         after Nuitka compilation.")
            print("="*70 + "\n")
            args.anti_debug = None
        
        if args.import_obf:
            print("\n" + "="*70)
            print("WARNING: Import obfuscation is incompatible with Nuitka EXE packaging.")
            print("         Import obfuscation has been disabled.")
            print("         For production protection, use protectors like Themida/VMProtect")
            print("         after Nuitka compilation.")
            print("="*70 + "\n")
            args.import_obf = False

    obfuscator = PyObfuscator(
        project_path=args.project_path,
        entry_point=args.entry_point,
        entry_function=args.entry_function,
        output_dir=args.output_dir,
        remap=args.remap,
        anti_debug=args.anti_debug,
        string_prot=args.string_prot,
        num_obf=args.num_obf,
        import_obf=args.import_obf,
        state_machine=args.state_machine,
        builtin_dispatcher=args.builtin_dispatcher,
        name_gen=args.name_gen,
        enable_nuitka=args.nuitka,
        nuitka_onefile=args.nuitka_onefile,
        nuitka_standalone=args.nuitka_standalone,
        nuitka_output_name=args.nuitka_output_name,
        nuitka_disable_console=args.nuitka_disable_console,
        nuitka_icon=args.nuitka_icon,
        nuitka_admin=args.nuitka_admin,
        nuitka_plugins=args.nuitka_plugins,
        nuitka_extra_imports=args.nuitka_extra_imports,
        nuitka_options=args.nuitka_options,
    )

    obfuscator.run_obfuscation(args.banner)


if __name__ == "__main__":
    main()