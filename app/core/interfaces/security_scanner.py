from abc import ABC, abstractmethod

from app.core.models.security import SecurityResult


class SecurityScanner(ABC):
    """Contract for static dangerous-code detection. Implemented by Junior 2.

    Language-aware rules belong inside the scanner implementation, not the core.
    """

    @abstractmethod
    def scan(self, code: str, language: str) -> SecurityResult:
        """Return SAFE or SECURITY_VIOLATION. Do not execute the code."""
