from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.core.models.enums import ExecutionStatus, SecurityStatus, TestCaseStatus
from app.core.models.sandbox import SandboxResult
from app.core.models.security import SecurityResult
from app.core.services.queue import InMemoryJobQueue
from app.main import create_app
from app.registry.in_memory import InMemoryPluginRegistry
from tests.fakes import FakePlugin, FakeScanner, ScriptedSandbox


@contextmanager
def api_client(plugin=None, scanner=None, sandbox=None, extra_plugins=None):
    registry = InMemoryPluginRegistry()
    plugin = plugin or FakePlugin()
    registry.register(plugin)
    for extra in extra_plugins or []:
        registry.register(extra)
    if sandbox is None:
        sandbox = ScriptedSandbox([SandboxResult(exit_code=0, stdout="4")])
    app = create_app(
        settings=Settings(job_wait_timeout_seconds=5, queue_backend="memory"),
        plugin_registry=registry,
        security_scanner=scanner or FakeScanner(),
        sandbox_executor=sandbox,
        queue=InMemoryJobQueue(),
    )
    with TestClient(app) as client:
        yield client


def test_health():
    with api_client() as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_language_discovery():
    with api_client(
        plugin=FakePlugin(name="python", version="3.x"),
        extra_plugins=[FakePlugin(name="c", version="gcc")],
        sandbox=ScriptedSandbox([SandboxResult(exit_code=0, stdout="")]),
    ) as client:
        response = client.get("/api/v1/languages")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["languages"]}
    assert names == {"python", "c"}


def test_api_successful_execution():
    with api_client(sandbox=ScriptedSandbox([SandboxResult(exit_code=0, stdout="4")])) as client:
        response = client.post(
            "/api/v1/executions",
            json={
                "language": "python",
                "code": "print(int(input())*2)",
                "test_cases": [{"input": "2", "expected_output": "4"}],
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ExecutionStatus.COMPLETED
    assert body["passed_test_cases"] == 1
    assert body["results"][0]["status"] == TestCaseStatus.PASSED


def test_api_invalid_request_missing_test_cases():
    with api_client() as client:
        response = client.post(
            "/api/v1/executions",
            json={"language": "python", "code": "print(1)", "test_cases": []},
        )
    assert response.status_code == 422
    assert "error" in response.json()


def test_api_unsupported_language():
    with api_client() as client:
        response = client.post(
            "/api/v1/executions",
            json={
                "language": "java",
                "code": "class A {}",
                "test_cases": [{"input": "1", "expected_output": "1"}],
            },
        )
    assert response.status_code == 422
    assert "Unsupported language" in response.json()["error"]


def test_api_security_violation():
    with api_client(
        scanner=FakeScanner(
            SecurityResult(status=SecurityStatus.SECURITY_VIOLATION, reason="eval")
        )
    ) as client:
        response = client.post(
            "/api/v1/executions",
            json={
                "language": "python",
                "code": "eval('1')",
                "test_cases": [{"input": "1", "expected_output": "1"}],
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == ExecutionStatus.SECURITY_VIOLATION
