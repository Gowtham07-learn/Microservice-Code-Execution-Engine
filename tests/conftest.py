from app.config.settings import Settings
from app.core.engine.orchestrator import ExecutionOrchestrator
from app.core.models.request import ExecutionRequest, TestCase
from app.registry.in_memory import InMemoryPluginRegistry
from tests.fakes import FakePlugin, FakeScanner, ScriptedSandbox


def settings(**kwargs) -> Settings:
    return Settings(**kwargs)


def request_python(*outputs_as_cases: tuple[str, str]) -> ExecutionRequest:
    cases = [
        TestCase(input=stdin, expected_output=expected)
        for stdin, expected in outputs_as_cases
    ]
    return ExecutionRequest(
        language="python",
        code="print(int(input()) * 2)",
        test_cases=cases,
    )


def build_orchestrator(plugin=None, scanner=None, sandbox=None, compile_argv=None):
    registry = InMemoryPluginRegistry()
    plugin = plugin or FakePlugin(compile_argv=compile_argv)
    registry.register(plugin)
    scanner = scanner or FakeScanner()
    orchestrator = ExecutionOrchestrator(
        plugin_registry=registry,
        security_scanner=scanner,
        sandbox_executor=sandbox,
        execution_config=settings().execution_config(),
    )
    return orchestrator, registry, plugin, scanner
