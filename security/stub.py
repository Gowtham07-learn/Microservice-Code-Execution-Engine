from app.core.interfaces.security_scanner import SecurityScanner
from app.core.models.enums import SecurityStatus
from app.core.models.security import SecurityResult


class StubSecurityScanner(SecurityScanner):
    """Placeholder until Junior 2 implements language-aware static scanning.

    Always returns SAFE so the core lifecycle can be wired. Replace this class
    in app.main.build_container once the real scanner is ready.
    """

    def scan(self, code: str, language: str) -> SecurityResult:
        return SecurityResult(status=SecurityStatus.SAFE)
