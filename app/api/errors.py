from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import RequestValidationError, UnsupportedLanguageError


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_domain_validation(_request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": str(exc), "details": exc.details},
        )

    @app.exception_handler(UnsupportedLanguageError)
    async def handle_unsupported(_request: Request, exc: UnsupportedLanguageError):
        return JSONResponse(
            status_code=422,
            content={
                "error": "Unsupported language",
                "details": [f"language '{exc.language}' is not registered"],
            },
        )

    @app.exception_handler(FastAPIRequestValidationError)
    async def handle_pydantic(_request: Request, exc: FastAPIRequestValidationError):
        details = []
        for err in exc.errors():
            loc = ".".join(str(part) for part in err.get("loc", []) if part != "body")
            details.append(f"{loc}: {err.get('msg')}" if loc else str(err.get("msg")))
        return JSONResponse(
            status_code=422,
            content={"error": "Invalid request body", "details": details},
        )

    @app.exception_handler(HTTPException)
    async def handle_http(_request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )
