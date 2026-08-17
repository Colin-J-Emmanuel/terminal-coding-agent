"""
CodeValidator: static safety check run BEFORE any code executes.

Parses code into an AST and flags dangerous imports. This is defense in
depth, not a hard security boundary — a determined adversary can evade
pure-Python checks. Real isolation comes from the sandboxed executor.
"""

import ast

class CodeValidator:
    DANGEROUS_MODULES = {"os", "subprocess", "socket", "sys"}

    def validate(self, code):
        """
        Check code for dangerous patterns.
        
        Returns {"safe": bool, "violations": [...]}.
        A syntax error counts as unsafe - we won't run code we can't parse
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"safe": False, "violations": [f"Syntax error: {e}"]}
        
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DANGEROUS_MODULES:
                        violations.append(f"Dangerous import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.DANGEROUS_MODULES:
                    violations.append(f"Dangerous import: {node.module}")

        return {"safe": len(violations) == 0, "violations": violations}
    
if __name__ == "__main__":
    v = CodeValidator()
    tests = [
        "print('hello)",                        # safe
        "import os",                            # dangerous (Import)
        "from subprocess import run",           # dangerous (ImportFrom)
        "import math, socket",                  # one safe, one dangerous
        "print('unclosed"                       # syntax error
    ]
    for t in tests:
        print(repr(t), "->", v.validate(t))