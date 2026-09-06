# Extensible Code Execution Microservice

## 1. Overview

This project is a small code-execution backend, similar in role to the judge that runs submissions on platforms such as LeetCode. A client sends source code, a language, and test cases. The service runs the program against every test case in isolation and returns pass/fail results.

The core engine is language-agnostic. Python and C are plugins. Security scanning and Docker isolation are separate modules so two junior developers can implement them without changing orchestration logic.

## 2. Problem Statement

The engine must:

- Accept source code, a programming language, and multiple test cases
- Execute the program against every test case
- Return PASSED/FAILED (and other error statuses) per test case
- Return actual output and expected output
- Return total / passed / failed counts
- Support Python and C through a plugin architecture
- Allow adding a language such as C++ without rewriting the core
- Perform basic dangerous-code detection
- Isolate untrusted code and enforce timeout plus resource limits
- Expose a microservice API
- Be designed so workers can scale toward 100+ executions per second
- Stay simple enough to explain in a CSEA evaluation

## 3. Features

- Python execution (Junior 1 plugin)
- C execution with compile-once per submission (Junior 1 plugin)
- Multiple test cases and result evaluation in the core
- Plugin architecture and plugin registry
- Security scanning contract (Junior 2)
- Docker sandbox contract (Junior 2)
- Timeout and resource limits passed as `ExecutionConfig` (not hard-coded in the core)
- REST API: execute, list languages, health
- Queue + worker architecture (in-memory locally, Redis in Docker Compose)

## 4. Architecture

```
Client
 ↓
API
 ↓
Execution Engine
 ↓
Plugin Registry
 ↓
Security Scanner
 ↓
Queue
 ↓
Execution Worker
 ↓
Sandbox
 ↓
Program
 ↓
Test Evaluator
 ↓
Result
```

Two processes, one repository:

- **API service** — validation, enqueue, wait for result, HTTP
- **Execution worker** — security scan, plugin prepare/compile, sandbox runs, aggregation

Untrusted code never runs inside the API process.

## 5. Project Structure

| Path | Role |
|---|---|
| `app/api/` | HTTP routes, request/response schemas, error handlers |
| `app/core/engine/` | Orchestrator, output comparison, aggregation |
| `app/core/interfaces/` | `LanguagePlugin`, `SecurityScanner`, `SandboxExecutor`, `JobQueue` |
| `app/core/models/` | Language-independent domain models |
| `app/core/services/` | Validation, queue implementations, API facade |
| `app/registry/` | In-memory registry and plugin bootstrap |
| `app/workers/` | Worker loop |
| `app/config/` | Environment-backed settings |
| `plugins/python`, `plugins/c` | Junior 1 — set `PLUGIN_READY = True` when implemented |
| `security/` | Junior 2 scanner |
| `sandbox/` | Junior 2 Docker executor |
| `tests/unit/` | Core tests with mocks |
| `tests/integration/` | Skipped until juniors integrate |
| `docs/` | Architecture and API notes |

## 6. Technology Stack

- Python 3.12
- FastAPI + Pydantic
- Uvicorn
- pytest
- Redis (optional; used in Docker Compose)
- Docker Compose

No database, authentication, or frontend.

## 7. Setup

```bash
git clone <repository>
cd "CODE ENGINE"

python -m venv .venv
```

Activate the environment:

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (bash): `source .venv/Scripts/activate`
- Linux/macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
cp .env.example .env
```

Important variables in `.env`:

| Variable | Meaning |
|---|---|
| `QUEUE_BACKEND` | `memory` (local) or `redis` (compose) |
| `REDIS_URL` | Redis connection when using `redis` |
| `TIMEOUT_SECONDS` | Per-run sandbox timeout |
| `MEMORY_LIMIT_MB` | Memory cap passed to the sandbox |
| `CPU_LIMIT` | CPU cap passed to the sandbox |
| `MAX_OUTPUT_BYTES` | Stdout/stderr cap |
| `MAX_PROCESSES` | Process cap |
| `MAX_CODE_BYTES` | Request code size limit |
| `MAX_TEST_CASES` | Request test-case count limit |

## 8. Running the Project

Local (API + in-process worker):

```bash
uvicorn app.main:app --reload --port 8000
```

The API listens on **http://127.0.0.1:8000**.

Docker Compose (API + Redis + worker):

```bash
docker compose up --build
```

| Service | Port |
|---|---|
| `api` | 8000 |
| `redis` | 6379 |
| `worker` | none (consumes the queue) |

Until Junior 1 sets `PLUGIN_READY = True`, `GET /api/v1/languages` returns an empty list and executions for python/c are rejected as unsupported. Until Junior 2 implements the sandbox, even wired plugins cannot run real user code (the stub sandbox returns `SYSTEM_ERROR` by design).

## 9. Health Check

`GET /health`

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status": "healthy"}
```

## 10. Check Supported Languages

`GET /api/v1/languages`

```bash
curl http://127.0.0.1:8000/api/v1/languages
```

After plugins are registered:

```json
{
  "languages": [
    {"name": "c", "version": "gcc"},
    {"name": "python", "version": "3.x"}
  ]
}
```

## 11. Execute Python

```bash
curl -X POST http://127.0.0.1:8000/api/v1/executions \
  -H "Content-Type: application/json" \
  -d "{\"language\":\"python\",\"code\":\"n = int(input())\\nprint(n * 2)\",\"test_cases\":[{\"input\":\"2\",\"expected_output\":\"4\"},{\"input\":\"5\",\"expected_output\":\"10\"},{\"input\":\"7\",\"expected_output\":\"20\"}]}"
```

## 12. Execute C

```bash
curl -X POST http://127.0.0.1:8000/api/v1/executions \
  -H "Content-Type: application/json" \
  -d "{\"language\":\"c\",\"code\":\"#include <stdio.h>\\nint main(){int n; scanf(\\\"%d\\\", &n); printf(\\\"%d\\\\n\\\", n*2); return 0;}\",\"test_cases\":[{\"input\":\"2\",\"expected_output\":\"4\"},{\"input\":\"5\",\"expected_output\":\"10\"}]}"
```

C is compiled **once** per request, then the binary is run once per test case.

## 13. Error Testing

Wrong output: use expected `"20"` for input `"7"` with `print(n * 2)` → test case `FAILED`, overall `COMPLETED`.

Compilation error: send invalid C (missing brace). Expect `COMPILATION_ERROR` and no per-test execution.

Runtime error: Python `print(1/0)` → test case `RUNTIME_ERROR`.

Timeout: `while True: pass` → `TIME_LIMIT_EXCEEDED` after `TIMEOUT_SECONDS`.

Dangerous code: e.g. `os.system(...)` once Junior 2 scanner rules exist → `SECURITY_VIOLATION` and **no sandbox run**.

## 14. Running Tests

```bash
pytest
```

Core unit tests mock `LanguagePlugin`, `SecurityScanner`, and `SandboxExecutor`. Integration tests are skipped until Junior 1 and Junior 2 land.

## 15. Adding a New Language

1. Create `plugins/cpp/plugin.py` with a `CppPlugin` that implements `LanguagePlugin`.
2. Implement `language`, `version`, `validate`, `prepare`, `compile_command`, `run_command`.
3. Set `PLUGIN_READY = True`.
4. Register it in `app/registry/bootstrap.py` the same way as Python and C.

The orchestrator does not contain `if language == "python"` branches. Output comparison stays in the core.

## 16. Scalability

```
API 1 ─┐
API 2 ─┼→ Queue → Worker 1 → Sandbox
API 3 ─┘          Worker 2
                  Worker N
```

The API is stateless. Heavy work is on workers. To approach 100+ executions/second, add worker replicas (`docker compose up --scale worker=N`) and keep sandbox overhead in mind. Extra API instances alone will not help if workers are saturated. This project does not claim 100 exec/s on a laptop; it is designed so capacity scales with workers.

## 17. Security

Two layers:

1. **Static scan** (`SecurityScanner`) — reject dangerous patterns before any run.
2. **Sandbox** (`SandboxExecutor`) — isolate the process, disable network, enforce CPU/memory/output/process limits and timeout.

This is **not** a production-grade sandbox. It is enough to demonstrate isolation thinking for the challenge.

## 18. Team Responsibilities

**Third-year lead:** architecture, core engine, API, models, plugin/security/sandbox integration, test-case orchestration, queue/workers, core tests, README, docs.

**Junior 1:** `PythonPlugin`, `CPlugin`, `LanguagePlugin` implementations, language-specific prepare/compile/run.

**Junior 2:** `SecurityScanner` with language-aware rules, Docker sandbox, timeout, CPU/memory/output/process limits, container cleanup.

## 19. Limitations

- Real Python/C execution depends on Junior 1 plugins and Junior 2 sandbox.
- Static scanning is basic, not a security boundary by itself.
- In-memory queue cannot share work across machines.
- No job history, auth, or persistent storage.
- Sandbox quality is bounded by the Docker setup Junior 2 provides.

## 20. Future Improvements

- More languages (C++, Java)
- Stronger sandboxing (seccomp, gVisor, dropped capabilities)
- Distributed workers with metrics
- Persistent job storage and async job IDs
- Monitoring and structured stage tracking
