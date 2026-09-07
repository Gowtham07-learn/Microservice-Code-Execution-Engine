# Language Plugins

## 1. Interface

The core talks to languages only through `LanguagePlugin`:

```text
LanguagePlugin
  language()
  version()
  validate(code)
  prepare(code, workspace)
  compile_command(prepared)
  run_command(prepared)
```

Plugins prepare files and command arguments. They do not compare stdout with
expected output, run Docker, scan for dangerous code, aggregate test cases, or
own API behavior.

## 2. Architecture

```text
Core
  |
  v
PluginRegistry
  |
  v
LanguagePlugin
  |-- PythonPlugin
  |-- CPlugin
```

`PluginRegistry` stores plugin instances by their canonical lowercase language
id. The core asks the registry for a plugin and then calls the interface above.
Unsupported languages return no plugin, and request validation turns that into a
clean `UnsupportedLanguageError`.

## 3. PythonPlugin

`PythonPlugin` accepts Python source, validates syntax with `ast.parse`, writes
`main.py` into the workspace, and returns:

```text
compile_command -> None
run_command     -> ["python", "main.py"]
```

Python syntax errors raise `PluginValidationError`, which the orchestrator maps
to `COMPILATION_ERROR`. Runtime errors, stderr, exit code, and timeout are
reported by the `SandboxExecutor` during the run phase and mapped by the core.

## 4. CPlugin

`CPlugin` writes `main.c` into the workspace and prepares an executable named
`main`. It returns:

```text
compile_command -> ["gcc", "main.c", "-O2", "-std=c11", "-Wall", "-Wextra", "-o", "main"]
run_command     -> ["./main"]
```

The orchestrator executes the compile command once in the sandbox. If GCC
returns a non-zero exit code, the request stops with `COMPILATION_ERROR`. If
compilation succeeds, the same executable is run once per test case.

## 5. Execution Lifecycle

1. API validates request shape and registered language.
2. Worker asks `PluginRegistry` for the requested plugin.
3. `SecurityScanner` scans the source before any sandbox command runs.
4. Plugin validates and prepares files in a temporary workspace.
5. Core asks the plugin for an optional compile command.
6. `SandboxExecutor` runs compilation once when needed.
7. Core asks the plugin for the run command.
8. `SandboxExecutor` runs the program once per test case with stdin.
9. Core normalizes stdout, compares it to expected output, and aggregates.
10. Temporary workspace cleanup happens in the orchestrator.

## 6. Error Handling

| Situation | Owner | Result |
|---|---|---|
| Python syntax error | PythonPlugin validate | `COMPILATION_ERROR` |
| C compiler failure | GCC via sandbox | `COMPILATION_ERROR` |
| Program non-zero exit | Sandbox result + core | per-test `RUNTIME_ERROR` |
| Timeout | Sandbox result + core | `TIME_LIMIT_EXCEEDED` |
| Dangerous code | SecurityScanner | `SECURITY_VIOLATION` |
| Sandbox/infrastructure failure | Sandbox/core | `SYSTEM_ERROR` |
| Wrong stdout | Core evaluator | per-test `FAILED` |

## 7. Adding C++

Create a new plugin that implements `LanguagePlugin`:

```python
class CppPlugin(LanguagePlugin):
    def language(self) -> str:
        return "cpp"

    def version(self) -> str:
        return "g++"

    def validate(self, code: str) -> None:
        if not code.strip():
            raise PluginValidationError("C++ source code is empty")

    def prepare(self, code: str, workspace: Path) -> PreparedProgram:
        source = workspace / "main.cpp"
        artifact = workspace / "main"
        source.write_text(code, encoding="utf-8")
        return PreparedProgram(workspace=workspace, source_path=source, artifact_path=artifact)

    def compile_command(self, prepared: PreparedProgram) -> list[str]:
        return ["g++", "main.cpp", "-O2", "-std=c++17", "-o", "main"]

    def run_command(self, prepared: PreparedProgram) -> list[str]:
        return ["./main"]
```

Then register it:

```python
registry.register(CppPlugin())
```

No output comparison, API route, orchestrator branch, queue code, or sandbox
code changes are required.

## 8. Testing

Language plugin unit tests cover syntax validation, file preparation, compile
commands, run commands, stdout/stderr propagation through the orchestrator,
runtime errors, timeouts, compilation errors, multiple executions, and compile
once for C. Registry tests cover Python/C lookup, supported-language listing,
unsupported-language errors, and registering a new plugin.
