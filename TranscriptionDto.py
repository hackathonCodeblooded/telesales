from uuid import UUID

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TranscriptDTO(BaseModel):
    transcript: str
    agent_id: Optional[str] = None
    customer_phone_number: Optional[str] = None
    audio_s3_path: Optional[str] = None
    business_insights: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None