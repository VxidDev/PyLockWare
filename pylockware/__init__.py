"""
PyLockWare - Python Obfuscation Suite
A comprehensive tool for obfuscating Python code with multiple protection layers.
"""
from .core import ModuleBase, PyObfuscator
from .modules import (
    RemapModule,
    StringProtectModule,
    NumberObfModule,
    AntiDebugModule,
    ImportObfuscateModule,
    StateMachineModule
)

__version__ = "2.0.0"
__all__ = [
    'ModuleBase',
    'PyObfuscator',
    'RemapModule',
    'StringProtectModule',
    'NumberObfModule',
    'AntiDebugModule',
    'ImportObfuscateModule',
    'StateMachineModule'
]