from pydantic import BaseModel, Field

class ExtractedInfo(BaseModel):
    http_statuses: list[str] = Field(default_factory=list)
    error_codes: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    key_error_lines: list[str] = Field(default_factory=list)