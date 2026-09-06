from pathlib import Path

from app.core.interfaces.language_plugin import LanguagePlugin
from app.core.interfaces.sandbox_executor import SandboxExecutor
from app.core.interfaces.security_scanner import SecurityScanner
from app.core.models.enums import SecurityStatus
from app.core.models.plugin import PreparedProgram
from app.core.models.sandbox import ExecutionConfig, SandboxResult
from app.core.models.security import SecurityResult


class FakePlugin(LanguagePlugin):
    def __init__(
        self,
        name: str = "python",
        version: str = "3.x",
        compile_argv: list[str] | None = None,
    ) -> None:
        self._name = name
        self._version = version
        self._compile_argv = compile_argv
        self.prepare_calls = 0
        self.compile_calls = 0

    def language(self) -> str:
        return self._name

    def version(self) -> str:
        return self._version

    def validate(self, code: str) -> None:
        return None

    def prepare(self, code: str, workspace: Path) -> PreparedProgram:
        self.prepare_calls += 1
        source = workspace / "main.src"
        source.write_text(code, encoding="utf-8")
        return PreparedProgram(workspace=workspace, source_path=source)

    def compile_command(self, prepared: PreparedProgram) -> list[str] | None:
        self.compile_calls += 1
        return self._compile_argv

    def run_command(self, prepared: PreparedProgram) -> list[str]:
        return ["run"]


class FakeScanner(SecurityScanner):
    def __init__(self, result: SecurityResult | None = None) -> None:
        self.result = result or SecurityResult(status=SecurityStatus.SAFE)
        self.calls: list[tuple[str, str]] = []

    def scan(self, code: str, language: str) -> SecurityResult:
        self.calls.append((code, language))
        return self.result


class ScriptedSandbox(SandboxExecutor):
    """Returns sandbox results in order. Extra calls reuse the last result."""

    def __init__(self, responses: list[SandboxResult]) -> None:
        self.responses = list(responses)
        self.commands: list[list[str]] = []
        self.stdins: list[str] = []

    def execute(
        self,
        command: list[str],
        stdin: str,
        config: ExecutionConfig,
        workspace: Path,
    ) -> SandboxResult:
        self.commands.append(command)
        self.stdins.append(stdin)
        if not self.responses:
            raise AssertionError("Sandbox called more times than scripted")
        return self.responses.pop(0)
