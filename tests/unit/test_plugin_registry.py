import pytest

from app.core.exceptions import UnsupportedLanguageError
from app.core.interfaces.language_plugin import LanguagePlugin
from app.core.models.plugin import PreparedProgram
from app.core.models.request import ExecutionRequest, TestCase
from app.core.services.validation import RequestValidator
from app.registry.bootstrap import register_plugins
from app.registry.in_memory import InMemoryPluginRegistry
from tests.conftest import settings


def test_python_lookup():
    registry = InMemoryPluginRegistry()
    register_plugins(registry)

    plugin = registry.get("python")

    assert plugin is not None
    assert plugin.language() == "python"


def test_c_lookup():
    registry = InMemoryPluginRegistry()
    register_plugins(registry)

    plugin = registry.get("c")

    assert plugin is not None
    assert plugin.language() == "c"


def test_supported_language_list():
    registry = InMemoryPluginRegistry()
    register_plugins(registry)

    assert registry.list_supported_languages() == ["c", "python"]


def test_unsupported_language_is_clean_error():
    registry = InMemoryPluginRegistry()
    register_plugins(registry)
    validator = RequestValidator(registry, settings())

    with pytest.raises(UnsupportedLanguageError) as exc_info:
        validator.validate(
            ExecutionRequest(
                language="rust",
                code="fn main() {}",
                test_cases=[TestCase(input="", expected_output="")],
            )
        )

    assert exc_info.value.language == "rust"
    assert registry.get("rust") is None


def test_registering_a_new_plugin():
    class CppPlugin(LanguagePlugin):
        def language(self) -> str:
            return "cpp"

        def version(self) -> str:
            return "g++"

        def validate(self, code: str) -> None:
            return None

        def prepare(self, code: str, workspace):
            source_path = workspace / "main.cpp"
            return PreparedProgram(workspace=workspace, source_path=source_path)

        def compile_command(self, prepared: PreparedProgram) -> list[str] | None:
            return ["g++", "main.cpp", "-o", "main"]

        def run_command(self, prepared: PreparedProgram) -> list[str]:
            return ["./main"]

    registry = InMemoryPluginRegistry()
    plugin = CppPlugin()

    registry.register(plugin)

    assert registry.get("cpp") is plugin
    assert registry.list_supported_languages() == ["cpp"]
