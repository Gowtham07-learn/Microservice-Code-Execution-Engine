from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import install_error_handlers
from app.api.routes.executions import router as executions_router
from app.api.routes.health import router as health_router
from app.api.routes.languages import router as languages_router
from app.config.settings import Settings, get_settings
from app.core.engine.orchestrator import ExecutionOrchestrator
from app.core.services.execution_service import ExecutionService
from app.core.services.queue import InMemoryJobQueue, RedisJobQueue
from app.core.services.validation import RequestValidator
from app.registry.bootstrap import register_plugins
from app.registry.in_memory import InMemoryPluginRegistry
from app.workers.worker import run_worker_loop
from sandbox.stub import StubSandboxExecutor
from security.stub import StubSecurityScanner


def build_container(settings: Settings | None = None, **overrides):
    settings = settings or get_settings()
    registry = overrides.get("plugin_registry") or InMemoryPluginRegistry()
    if "plugin_registry" not in overrides:
        register_plugins(registry)

    scanner = overrides.get("security_scanner") or _load_scanner()
    sandbox = overrides.get("sandbox_executor") or _load_sandbox()
    queue = overrides.get("queue")
    if queue is None:
        queue = _build_queue(settings)

    orchestrator = overrides.get("orchestrator") or ExecutionOrchestrator(
        plugin_registry=registry,
        security_scanner=scanner,
        sandbox_executor=sandbox,
        execution_config=settings.execution_config(),
    )
    validator = overrides.get("request_validator") or RequestValidator(registry, settings)
    execution_service = overrides.get("execution_service") or ExecutionService(
        queue, settings.job_wait_timeout_seconds
    )
    return {
        "settings": settings,
        "plugin_registry": registry,
        "security_scanner": scanner,
        "sandbox_executor": sandbox,
        "queue": queue,
        "orchestrator": orchestrator,
        "request_validator": validator,
        "execution_service": execution_service,
    }


def _load_scanner():
    try:
        from security.scanner import SCANNER_READY, DefaultSecurityScanner

        if SCANNER_READY:
            return DefaultSecurityScanner()
    except (ImportError, NotImplementedError, TypeError):
        pass
    return StubSecurityScanner()


def _load_sandbox():
    try:
        from sandbox.executor import SANDBOX_READY, DockerSandboxExecutor

        if SANDBOX_READY:
            return DockerSandboxExecutor()
    except (ImportError, NotImplementedError, TypeError):
        pass
    return StubSandboxExecutor()


def _build_queue(settings: Settings):
    backend = settings.queue_backend.lower()
    if backend == "redis":
        from redis.asyncio import Redis

        client = Redis.from_url(settings.redis_url, decode_responses=True)
        return RedisJobQueue(client, settings.job_result_ttl_seconds)
    return InMemoryJobQueue()


def create_app(settings: Settings | None = None, **overrides) -> FastAPI:
    container = build_container(settings, **overrides)
    settings = container["settings"]

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker_task = None
        queue = container["queue"]
        if isinstance(queue, InMemoryJobQueue):
            import asyncio

            worker_task = asyncio.create_task(
                run_worker_loop(queue, container["orchestrator"])
            )
        yield
        if worker_task is not None:
            worker_task.cancel()

    application = FastAPI(
        title="Extensible Code Execution Microservice",
        version="1.0.0",
        lifespan=lifespan,
    )
    for key, value in container.items():
        setattr(application.state, key, value)

    install_error_handlers(application)
    application.include_router(health_router)
    application.include_router(languages_router)
    application.include_router(executions_router)
    return application


app = create_app()
