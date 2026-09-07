PLUGIN_READY = True

from pathlib import Path

from app.core.exceptions import PluginValidationError
from app.core.interfaces.language_plugin import LanguagePlugin
from app.core.models.plugin import PreparedProgram


class CPlugin(LanguagePlugin):
    """C-specific validation and compile/run command preparation.

    Compile once via compile_command(). The core reuses run_command() per test case.
    """

    PLUGIN_READY = True
    SOURCE_FILE = "main.c"
    EXECUTABLE_FILE = "main"

    def language(self) -> str:
        return "c"

    def version(self) -> str:
        return "gcc"

    def validate(self, code: str) -> None:
        if not code.strip():
            raise PluginValidationError("C source code is empty")

    def prepare(self, code: str, workspace: Path) -> PreparedProgram:
        workspace.mkdir(parents=True, exist_ok=True)
        source_path = workspace / self.SOURCE_FILE
        artifact_path = workspace / self.EXECUTABLE_FILE
        source_path.write_text(code, encoding="utf-8")
        return PreparedProgram(
            workspace=workspace,
            source_path=source_path,
            artifact_path=artifact_path,
        )

    def compile_command(self, prepared: PreparedProgram) -> list[str] | None:
        if prepared.artifact_path is None:
            raise PluginValidationError("C executable artifact path was not prepared")
        return [
            "gcc",
            prepared.source_path.name,
            "-O2",
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-o",
            prepared.artifact_path.name,
        ]

    def run_command(self, prepared: PreparedProgram) -> list[str]:
        if prepared.artifact_path is None:
            raise PluginValidationError("C executable artifact path was not prepared")
        return [f"./{prepared.artifact_path.name}"]
