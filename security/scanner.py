import ast
import re

from app.core.interfaces.security_scanner import SecurityScanner
from app.core.models.enums import SecurityStatus
from app.core.models.security import SecurityResult


SCANNER_READY = True


class DefaultSecurityScanner(SecurityScanner):
    """Language-aware static scanner for potentially dangerous operations."""

    PYTHON_DANGEROUS_MODULES = {
        "subprocess",
        "socket",
        "ctypes",
        "multiprocessing",
    }

    PYTHON_DANGEROUS_CALLS = {
        "eval",
        "exec",
        "compile",
        "__import__",
    }

    PYTHON_DANGEROUS_ATTRIBUTES = {
        "system",
        "popen",
        "spawn",
        "fork",
        "forkpty",
        "execl",
        "execle",
        "execlp",
        "execv",
        "execve",
        "execvp",
        "remove",
        "unlink",
        "rmdir",
        "rmtree",
    }

    C_DANGEROUS_PATTERNS = {
        r"\bsystem\s*\(": "system()",
        r"\bpopen\s*\(": "popen()",
        r"\bfork\s*\(": "fork()",
        r"\bvfork\s*\(": "vfork()",
        r"\bexecl\s*\(": "execl()",
        r"\bexecle\s*\(": "execle()",
        r"\bexeclp\s*\(": "execlp()",
        r"\bexecv\s*\(": "execv()",
        r"\bexecve\s*\(": "execve()",
        r"\bexecvp\s*\(": "execvp()",
        r"\bsocket\s*\(": "socket()",
        r"\bconnect\s*\(": "connect()",
        r"\baccept\s*\(": "accept()",
        r"\bbind\s*\(": "bind()",
        r"\blisten\s*\(": "listen()",
        r"\bremove\s*\(": "remove()",
        r"\bunlink\s*\(": "unlink()",
    }

    def scan(self, code: str, language: str) -> SecurityResult:
        language = language.lower().strip()

        if language in {"python", "py"}:
            return self._scan_python(code)

        if language == "c":
            return self._scan_c(code)

        return SecurityResult(status=SecurityStatus.SAFE)

    def _scan_python(self, code: str) -> SecurityResult:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Syntax errors are handled by the language plugin.
            return SecurityResult(status=SecurityStatus.SAFE)

        for node in ast.walk(tree):

            # eval(), exec(), compile(), __import__()
            if isinstance(node, ast.Call):

                if isinstance(node.func, ast.Name):
                    if node.func.id in self.PYTHON_DANGEROUS_CALLS:
                        return self._violation(
                            f"Use of {node.func.id}() is not allowed"
                        )

                # os.system(), os.popen(), etc.
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.PYTHON_DANGEROUS_ATTRIBUTES:
                        return self._violation(
                            f"Use of {node.func.attr}() is not allowed"
                        )

            # import subprocess / socket / etc.
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]

                    if module in self.PYTHON_DANGEROUS_MODULES:
                        return self._violation(
                            f"Import of {module} is not allowed"
                        )

            # from subprocess import ...
            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[0]

                if module in self.PYTHON_DANGEROUS_MODULES:
                    return self._violation(
                        f"Import of {module} is not allowed"
                    )

        return SecurityResult(status=SecurityStatus.SAFE)

    def _scan_c(self, code: str) -> SecurityResult:
        # Remove C comments to reduce simple false positives.
        cleaned = re.sub(
            r"/\*.*?\*/",
            "",
            code,
            flags=re.DOTALL,
        )

        cleaned = re.sub(
            r"//.*",
            "",
            cleaned,
        )

        for pattern, function_name in self.C_DANGEROUS_PATTERNS.items():
            if re.search(pattern, cleaned):
                return self._violation(
                    f"Use of {function_name} is not allowed"
                )

        return SecurityResult(status=SecurityStatus.SAFE)

    @staticmethod
    def _violation(reason: str) -> SecurityResult:
        return SecurityResult(
            status=SecurityStatus.SECURITY_VIOLATION,
            reason=reason,
        )