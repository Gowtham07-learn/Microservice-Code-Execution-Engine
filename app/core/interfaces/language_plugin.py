from abc import ABC, abstractmethod
from pathlib import Path

from app.core.models.plugin import PreparedProgram


class LanguagePlugin(ABC):
    """Contract for language-specific behavior. Implemented by Junior 1.

    The core never branches on language names. It only calls this interface.
    Plugins must not compare test-case output and must not invoke Docker.
    """

    @abstractmethod
    def language(self) -> str:
        """Canonical language id used in API requests, e.g. 'python' or 'c'."""

    @abstractmethod
    def version(self) -> str:
        """Human-readable runtime/compiler version label."""

    @abstractmethod
    def validate(self, code: str) -> None:
        """Reject obviously invalid source before prepare/compile.

        Raise PluginValidationError on failure.
        """

    @abstractmethod
    def prepare(self, code: str, workspace: Path) -> PreparedProgram:
        """Write source into workspace and return a reusable artifact descriptor."""

    @abstractmethod
    def compile_command(self, prepared: PreparedProgram) -> list[str] | None:
        """Return a compile argv, or None when the language is interpreted.

        The orchestrator runs this at most once per request, inside the sandbox.
        """

    @abstractmethod
    def run_command(self, prepared: PreparedProgram) -> list[str]:
        """Return argv used to run the program once per test case."""
