from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(..., examples=["VALIDATION_ERROR"])
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody
