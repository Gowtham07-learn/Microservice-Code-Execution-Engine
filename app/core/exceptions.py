class EngineError(Exception):
    """Base error for the execution core."""


class UnsupportedLanguageError(EngineError):
    def __init__(self, language: str) -> None:
        self.language = language
        super().__init__(f"Unsupported language: {language}")


class RequestValidationError(EngineError):
    def __init__(self, message: str, details: list[str] | None = None) -> None:
        self.details = details or []
        super().__init__(message)


class PluginValidationError(EngineError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
