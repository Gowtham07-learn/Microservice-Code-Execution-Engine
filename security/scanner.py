from app.core.interfaces.security_scanner import SecurityScanner
from app.core.models.enums import SecurityStatus
from app.core.models.security import SecurityResult

SCANNER_READY = False


class DefaultSecurityScanner(SecurityScanner):
    """Junior 2: language-aware static scanning.

    Return SAFE or SECURITY_VIOLATION. Do not execute the submitted program.
    Set SCANNER_READY = True when this implementation is complete.
    """

    def scan(self, code: str, language: str) -> SecurityResult:
        raise NotImplementedError(
            "Junior 2: implement DefaultSecurityScanner.scan"
        )
