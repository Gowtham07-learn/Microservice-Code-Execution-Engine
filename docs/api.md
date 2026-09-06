# API

Base URL (local): `http://127.0.0.1:8000`

Validation failures return HTTP 422:

```json
{
  "error": "Invalid execution request",
  "details": ["source code is required"]
}
```

Successful executions return HTTP 200 even when tests fail or security rejects the code. The `status` field describes the outcome.

---

## POST /api/v1/executions

**Purpose:** Run submitted code against every test case and return per-case plus aggregate results.

**Request**

```json
{
  "language": "python",
  "code": "n = int(input())\nprint(n * 2)",
  "test_cases": [
    {"input": "2", "expected_output": "4"},
    {"input": "5", "expected_output": "10"},
    {"input": "7", "expected_output": "20"}
  ]
}
```

**Response (example)**

```json
{
  "status": "COMPLETED",
  "total_test_cases": 3,
  "passed_test_cases": 2,
  "failed_test_cases": 1,
  "results": [
    {
      "test_case": 1,
      "status": "PASSED",
      "actual_output": "4",
      "expected_output": "4",
      "error_message": null
    },
    {
      "test_case": 2,
      "status": "PASSED",
      "actual_output": "10",
      "expected_output": "10",
      "error_message": null
    },
    {
      "test_case": 3,
      "status": "FAILED",
      "actual_output": "14",
      "expected_output": "20",
      "error_message": null
    }
  ],
  "error_message": null
}
```

**Overall `status`:** `COMPLETED`, `COMPILATION_ERROR`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `SECURITY_VIOLATION`, `SYSTEM_ERROR`.

**Per-test `status`:** `PASSED`, `FAILED`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, `SYSTEM_ERROR`.

**Errors**

| HTTP | When |
|---|---|
| 422 | Missing fields, empty `test_cases`, unsupported language, oversized code |
| 200 + `SECURITY_VIOLATION` | Scanner rejected the source |
| 200 + `COMPILATION_ERROR` | Compile/validate failed |
| 200 + `SYSTEM_ERROR` | Queue/worker/sandbox infrastructure failure |

**curl**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/executions \
  -H "Content-Type: application/json" \
  -d "{\"language\":\"python\",\"code\":\"print(int(input())*2)\",\"test_cases\":[{\"input\":\"2\",\"expected_output\":\"4\"}]}"
```

---

## GET /api/v1/languages

**Purpose:** Discover plugins currently registered. The list is not hard-coded in the API.

**Request:** none

**Response**

```json
{
  "languages": [
    {"name": "python", "version": "3.x"},
    {"name": "c", "version": "gcc"}
  ]
}
```

**Errors:** none expected (empty list if juniors have not registered plugins).

**curl**

```bash
curl http://127.0.0.1:8000/api/v1/languages
```

---

## GET /health

**Purpose:** Liveness check for the API process.

**Request:** none

**Response**

```json
{"status": "healthy"}
```

**curl**

```bash
curl http://127.0.0.1:8000/health
```
