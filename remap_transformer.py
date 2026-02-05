"""
AST Transformer for remapping identifiers in Python code
"""
import ast
import builtins


class GlobalRenamer(ast.NodeTransformer):
    """Renames global identifiers in AST nodes, excluding builtins."""

    def __init__(self, global_replacements=None):
        # Get all built-in names to protect them from renaming
        self.builtin_names = set(dir(builtins)) | {
            "self",
            "cls",  # Common method/class parameters
            "args",
            "kwargs",  # Common function parameters
            "_"
        }
        # Only include non-builtin names in replacements
        self.global_replacements = {
            k: v
            for k, v in (global_replacements or {}).items()
            if k not in self.builtin_names
        }

    def visit_Import(self, node):
        for alias in node.names:
            # Don't rename imports of builtin modules
            if alias.name.split(".")[0] in self.builtin_names:
                continue
            if alias.asname and alias.asname in self.global_replacements:
                alias.asname = self.global_replacements[alias.asname]
        return node

    def visit_ImportFrom(self, node):
        # Don't rename imports from builtin modules
        if node.module and any(
            node.module == name or node.module.startswith(f"{name}.")
            for name in self.builtin_names
        ):
            return node

        for alias in node.names:
            old = alias.name
            if old in self.global_replacements:
                alias.name = self.global_replacements[old]
            if alias.asname and alias.asname in self.global_replacements:
                alias.asname = self.global_replacements[alias.asname]
        return node

    def visit_Attribute(self, node):
        # Rename attribute names if they're in the remap map
        # Only rename the attribute part (not the value part)
        if node.attr in self.global_replacements:
            node.attr = self.global_replacements[node.attr]
        # Visit the value part (the object whose attribute we're accessing)
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        # Don't rename builtin names
        if node.id in self.builtin_names:
            return node

        if isinstance(node.ctx, ast.Load) and node.id in self.global_replacements:
            node.id = self.global_replacements[node.id]
        elif isinstance(node.ctx, ast.Store) and node.id in self.global_replacements:
            node.id = self.global_replacements[node.id]
        elif isinstance(node.ctx, ast.Del) and node.id in self.global_replacements:
            node.id = self.global_replacements[node.id]
        return node

    def visit_FunctionDef(self, node):
        # Rename function name if it's in the remap map
        if node.name in self.global_replacements:
            node.name = self.global_replacements[node.name]
        # Visit the body of the function
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        # Rename async function name if it's in the remap map
        if node.name in self.global_replacements:
            node.name = self.global_replacements[node.name]
        # Visit the body of the function
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node):
        # Rename class name if it's in the remap map
        if node.name in self.global_replacements:
            node.name = self.global_replacements[node.name]
        # Visit the body of the class
        self.generic_visit(node)
        return node

    def visit_arg(self, node):
        # Rename function argument names if they're in the remap map
        if node.arg in self.global_replacements:
            node.arg = self.global_replacements[node.arg]
        # Visit annotation if present
        self.generic_visit(node)
        return node