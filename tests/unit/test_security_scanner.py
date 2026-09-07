from app.core.models.enums import SecurityStatus
from security.scanner import DefaultSecurityScanner


scanner = DefaultSecurityScanner()


def test_python_os_system_is_blocked():
    result = scanner.scan(
        'import os\nos.system("echo hello")',
        "python",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_python_subprocess_is_blocked():
    result = scanner.scan(
        "import subprocess\nsubprocess.run(['ls'])",
        "python",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_python_eval_is_blocked():
    result = scanner.scan(
        "eval('1 + 1')",
        "python",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_python_exec_is_blocked():
    result = scanner.scan(
        "exec('print(1)')",
        "python",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_python_socket_is_blocked():
    result = scanner.scan(
        "import socket\nsocket.socket()",
        "python",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_normal_python_is_safe():
    result = scanner.scan(
        "x = int(input())\nprint(x * 2)",
        "python",
    )
    assert result.status == SecurityStatus.SAFE


def test_c_system_is_blocked():
    result = scanner.scan(
        '#include <stdlib.h>\nint main() { system("ls"); }',
        "c",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_c_popen_is_blocked():
    result = scanner.scan(
        '#include <stdio.h>\nint main() { popen("ls", "r"); }',
        "c",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_c_fork_is_blocked():
    result = scanner.scan(
        '#include <unistd.h>\nint main() { fork(); }',
        "c",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_c_exec_is_blocked():
    result = scanner.scan(
        '#include <unistd.h>\nint main() { execvp("ls", 0); }',
        "c",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_c_network_is_blocked():
    result = scanner.scan(
        '#include <sys/socket.h>\nint main() { socket(2, 1, 0); }',
        "c",
    )
    assert result.status == SecurityStatus.SECURITY_VIOLATION


def test_normal_c_is_safe():
    result = scanner.scan(
        '#include <stdio.h>\nint main() { printf("Hello"); return 0; }',
        "c",
    )
    assert result.status == SecurityStatus.SAFE