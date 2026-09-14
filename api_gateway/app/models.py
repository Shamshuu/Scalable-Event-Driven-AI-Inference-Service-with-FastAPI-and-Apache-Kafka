from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class InferenceRequest(BaseModel):
    input_data: str = Field(min_length=1, max_length=100_000, description="Text, URL, or serialized model input")
    model_id: str = Field(default="default_model", min_length=1, max_length=200)

class InferenceResponse(BaseModel):
    request_id: str
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
    input_data: str
    output_data: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
