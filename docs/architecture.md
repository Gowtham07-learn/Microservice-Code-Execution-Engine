# Architecture

## 1. Problem

Build a LeetCode-style execution backend: submit code + language + test cases, run each case in isolation, return per-case and aggregate results, with plugin-based languages and basic safety.

## 2. Goals

- Language-agnostic core
- Clean contracts for plugins, security, and sandbox
- No untrusted execution in the API process
- Horizontal scale via queue + workers
- Simple enough for a third-year evaluation

## 3. High-level architecture

```
CLIENT → API SERVICE → VALIDATION → QUEUE → WORKER
                                          ↓
                                   Plugin Registry
                                          ↓
                                   Security Scanner
                                          ↓
                                   Language Plugin (prepare/compile)
                                          ↓
                                   Sandbox Executor
                                          ↓
                                   Test Evaluator (core)
                                          ↓
                                   Result → API
```

Logical microservices: **API** and **Worker**. Redis is the optional shared queue. Docker is the isolation mechanism (Junior 2), not a third business service.

## 4. Component responsibilities

| Component | Responsibility |
|---|---|
| API | HTTP, OpenAPI, wait for job result |
| RequestValidator | Size/presence checks, registered language |
| ExecutionService | Enqueue + wait |
| JobQueue | memory or Redis |
| ExecutionOrchestrator | Lifecycle |
| PluginRegistry | `get` / `list` / `register` |
| LanguagePlugin | Junior 1 |
| SecurityScanner | Junior 2 |
| SandboxExecutor | Junior 2 |
| TestEvaluator | Normalize and compare stdout |

## 5. Execution lifecycle

1. Validate request
2. Resolve plugin from registry
3. Enqueue
4. Worker: security scan — stop on `SECURITY_VIOLATION`
5. `plugin.validate` / `plugin.prepare`
6. If `compile_command` is not None, sandbox-compile **once**
7. For each test case, sandbox-run with stdin
8. Normalize + compare in core
9. Aggregate counts
10. Store result for the API waiter

## 6. Plugin architecture

`LanguagePlugin` methods: `language`, `version`, `validate`, `prepare`, `compile_command`, `run_command`.

The core never inspects language names. Python returns `compile_command = None`. C returns a gcc argv. Adding C++ is a new plugin + `registry.register`.

Bootstrap (`app/registry/bootstrap.py`) imports plugins only when `PLUGIN_READY` is True, so incomplete junior stubs do not crash the API.

## 7. API architecture

Synchronous HTTP for the client. Internally asynchronous via the queue so the API process stays off the sandbox CPU path.

Endpoints: `POST /api/v1/executions`, `GET /api/v1/languages`, `GET /health`.

## 8. Security architecture

Language-aware rules live in Junior 2’s scanner, selected by the `language` string. Plugins do not own security. Failed scans never reach the sandbox.

This is a pre-check, not a complete security boundary.

## 9. Sandbox architecture

The core passes `command`, `stdin`, `ExecutionConfig`, and `workspace`. It does not know Docker. Junior 2 should apply timeout, CPU, memory, output, process limits, disable network, and always clean up containers.

## 10. Queue / worker architecture

```
API 1 ─┐
API 2 ─┼→ Queue → Worker 1
API 3 ─┘          Worker N
```

- Local: `InMemoryJobQueue` + background asyncio worker inside uvicorn
- Compose: Redis list + dedicated worker process (`python -m app.workers.worker`)

Trade-off: in-memory is zero-infra and not multi-host. Redis is slightly more moving parts and is the scale path.

## 11. Error handling

| Situation | Status |
|---|---|
| Dangerous code | `SECURITY_VIOLATION` (no execute) |
| Compiler/parser failure | `COMPILATION_ERROR` |
| Non-zero program exit | per-test `RUNTIME_ERROR` |
| Sandbox timeout | per-test or compile `TIME_LIMIT_EXCEEDED` |
| Wrong stdout | per-test `FAILED`, overall `COMPLETED` |
| Infrastructure failure | `SYSTEM_ERROR` |

## 12. Scalability

100+ executions/second is an architecture target, not a laptop benchmark. Bottlenecks are sandbox start time, compile time, and worker count. Scale workers first. Keep the API stateless.

## 13. Extensibility

New language: implement `LanguagePlugin`, register it. New limits: change env / `ExecutionConfig`. New scanner: swap the injected `SecurityScanner`.

## 14. Testing strategy

Unit tests mock the three contracts and cover validation, plugin lookup, security short-circuit, pass/fail, multi-case aggregation, compile-once, runtime error, timeout, languages, health.

Integration tests wait for Junior 1 and Junior 2.

## 15. Trade-offs

- One repo, two processes instead of many microservices
- Sync HTTP instead of polling job IDs (simpler demo)
- Stub scanner/sandbox so the core is testable before juniors finish
- No database (not required)

## 16. Team module boundaries

Lead owns `app/`. Junior 1 owns `plugins/`. Junior 2 owns `security/` and `sandbox/`. Integration is constructor injection in `app.main.build_container`. If a junior module mismatches an ABC, add a thin adapter; do not rewrite the core.
