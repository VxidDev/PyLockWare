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
    parser.add_argument("--anti-debug", choices=['normal', 'strict'], help="Enable anti-debug and anti-injection protection ('normal' without thread checking, 'strict' with thread checking)")
    parser.add_argument("--string-prot", action="store_true", help="Enable string protection using base64 and zlib encoding")

    args = parser.parse_args()

    obfuscator = PyObfuscator(
        project_path=args.project_path,
        entry_point=args.entry_point,
        entry_function=args.entry_function,
        output_dir=args.output_dir,
        remap=args.remap,
        anti_debug=args.anti_debug,
        string_prot=args.string_prot,
    )

    obfuscator.run_obfuscation(args.banner)


if __name__ == "__main__":
    main()