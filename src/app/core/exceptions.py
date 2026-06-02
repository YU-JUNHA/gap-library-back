from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(code: str, message: str, status_code: int, details: dict | None = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def register_exception_handlers(app):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        code = "FORBIDDEN" if exc.status_code == 403 else "UNAUTHORIZED" if exc.status_code == 401 else "NOT_FOUND" if exc.status_code == 404 else "INTERNAL_ERROR"
        return error_response(code=code, message=str(exc.detail), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return error_response(
            code="VALIDATION_ERROR",
            message="요청 데이터가 올바르지 않습니다.",
            status_code=422,
            details={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, __: Exception):
        return error_response(
            code="INTERNAL_ERROR",
            message="서버 내부 오류가 발생했습니다.",
            status_code=500,
        )
