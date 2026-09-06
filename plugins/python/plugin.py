PLUGIN_READY = False
"""Set to True after Junior 1 implements this plugin. Bootstrap only registers ready plugins."""

from pathlib import Path

from app.core.interfaces.language_plugin import LanguagePlugin
from app.core.models.plugin import PreparedProgram


class PythonPlugin(LanguagePlugin):
    """Junior 1: implement Python-specific validate/prepare/run_command.

    Do not compare test-case output here. The core evaluator owns that.
    Do not invoke Docker here. The sandbox executor owns isolation.
    """

    def language(self) -> str:
        return "python"

    def version(self) -> str:
        return "3.x"

    def validate(self, code: str) -> None:
        raise NotImplementedError("Junior 1: implement PythonPlugin.validate")

    def prepare(self, code: str, workspace: Path) -> PreparedProgram:
        raise NotImplementedError("Junior 1: implement PythonPlugin.prepare")

    def compile_command(self, prepared: PreparedProgram) -> list[str] | None:
        return None

    def run_command(self, prepared: PreparedProgram) -> list[str]:
        raise NotImplementedError("Junior 1: implement PythonPlugin.run_command")
