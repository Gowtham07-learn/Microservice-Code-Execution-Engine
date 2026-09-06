PLUGIN_READY = False

from pathlib import Path

from app.core.interfaces.language_plugin import LanguagePlugin
from app.core.models.plugin import PreparedProgram


class CPlugin(LanguagePlugin):
    """Junior 1: implement C-specific validate/prepare/compile/run.

    Compile once via compile_command(). The core reuses run_command() per test case.
    """

    def language(self) -> str:
        return "c"

    def version(self) -> str:
        return "gcc"

    def validate(self, code: str) -> None:
        raise NotImplementedError("Junior 1: implement CPlugin.validate")

    def prepare(self, code: str, workspace: Path) -> PreparedProgram:
        raise NotImplementedError("Junior 1: implement CPlugin.prepare")

    def compile_command(self, prepared: PreparedProgram) -> list[str] | None:
        raise NotImplementedError("Junior 1: implement CPlugin.compile_command")

    def run_command(self, prepared: PreparedProgram) -> list[str]:
        raise NotImplementedError("Junior 1: implement CPlugin.run_command")
