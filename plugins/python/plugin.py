PLUGIN_READY = True
"""Bootstrap only registers ready plugins."""

import ast
from pathlib import Path

from app.core.exceptions import PluginValidationError
from app.core.interfaces.language_plugin import LanguagePlugin
from app.core.models.plugin import PreparedProgram


class PythonPlugin(LanguagePlugin):
    """Python-specific validation and command preparation.

    Do not compare test-case output here. The core evaluator owns that.
    Do not invoke Docker here. The sandbox executor owns isolation.
    """

    PLUGIN_READY = True
    SOURCE_FILE = "main.py"

    def language(self) -> str:
        return "python"

    def version(self) -> str:
        return "3.x"

    def validate(self, code: str) -> None:
        try:
            ast.parse(code)
        except SyntaxError as exc:
            location = f"line {exc.lineno}" if exc.lineno is not None else "unknown line"
            raise PluginValidationError(f"Python syntax error at {location}: {exc.msg}") from exc

    def prepare(self, code: str, workspace: Path) -> PreparedProgram:
        workspace.mkdir(parents=True, exist_ok=True)
        source_path = workspace / self.SOURCE_FILE
        source_path.write_text(code, encoding="utf-8")
        return PreparedProgram(workspace=workspace, source_path=source_path)

    def compile_command(self, prepared: PreparedProgram) -> list[str] | None:
        return None

    def run_command(self, prepared: PreparedProgram) -> list[str]:
        return ["python", prepared.source_path.name]
