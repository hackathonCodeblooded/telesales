from uuid import UUID

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TranscriptDTO(BaseModel):
    call_id: int
    transcript: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None