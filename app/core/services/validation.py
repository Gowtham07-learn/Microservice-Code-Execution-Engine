from app.core.exceptions import RequestValidationError, UnsupportedLanguageError
from app.core.interfaces.plugin_registry import PluginRegistry
from app.core.models.request import ExecutionRequest
from app.config.settings import Settings


class RequestValidator:
    def __init__(self, registry: PluginRegistry, settings: Settings) -> None:
        self._registry = registry
        self._settings = settings

    def validate(self, request: ExecutionRequest) -> None:
        errors: list[str] = []

        if not request.language or not request.language.strip():
            errors.append("language is required")
        if not request.code or not request.code.strip():
            errors.append("source code is required")
        if not request.test_cases:
            errors.append("test_cases must not be empty")

        if request.code and len(request.code.encode("utf-8")) > self._settings.max_code_bytes:
            errors.append(
                f"source code exceeds {self._settings.max_code_bytes} bytes"
            )

        if request.test_cases and len(request.test_cases) > self._settings.max_test_cases:
            errors.append(
                f"test_cases exceeds the maximum of {self._settings.max_test_cases}"
            )

        for index, case in enumerate(request.test_cases, start=1):
            if case.input is None:
                errors.append(f"test case {index} is missing input")
            elif len(case.input.encode("utf-8")) > self._settings.max_test_case_bytes:
                errors.append(f"test case {index} input is too large")
            if case.expected_output is None:
                errors.append(f"test case {index} is missing expected_output")
            elif len(case.expected_output.encode("utf-8")) > self._settings.max_test_case_bytes:
                errors.append(f"test case {index} expected_output is too large")

        if errors:
            raise RequestValidationError("Invalid execution request", errors)

        language = request.language.strip().lower()
        if self._registry.get(language) is None:
            raise UnsupportedLanguageError(language)
