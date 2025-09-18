from uuid import UUID

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TranscriptDTO(BaseModel):
    transcript: str
    agent_id: Optional[int] = None
    agent_name: Optional[str] = None
    customer_phone_number: Optional[str] = None
    audio_s3_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None

    # Fields from your notes
    call_id: Optional[str] = None
    agent_overall_rating: Optional[float] = None
    call_duration: Optional[float] = None
    customer_sentiment_score: Optional[float] = None
    conversation_quality_score: Optional[float] = None
    agent_tone_score: Optional[float] = None
    compliance_score: Optional[float] = None
    responsiveness_score: Optional[float] = None
    adaptability_score: Optional[float] = None
    product_awareness_score: Optional[float] = None
    problem_resolution_score: Optional[float] = None
    call_summarization: Optional[str] = None
    actionable_insights: Optional[List[str]] = None
    converted: Optional[bool] = None