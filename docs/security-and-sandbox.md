# Security and Sandbox

## 1. Overview

The code execution engine accepts untrusted user source code.

Security is implemented using two layers:

1. Static security scanning.
2. Isolated Docker execution.

Static scanning rejects known dangerous operations before execution. Docker provides an additional runtime isolation layer.

```text
             User Code
                 ↓
          Security Scanner
                 ↓
              SAFE?
             /     \
           NO       YES
           ↓         ↓
         Reject    Docker
                     ↓
                  Sandbox
                     ↓
                  Execute
                     ↓
                   Result