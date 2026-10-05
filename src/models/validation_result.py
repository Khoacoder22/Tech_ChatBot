from pydantic import BaseModel, Field

class ValidationResult(BaseModel):
    is_valid: bool
    score: int
    reasons: list[str] = Field(default_factory=list)