"""
Pydantic schemas for the /chat endpoint — request and response shapes
must match what the Next.js frontend sends and expects.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's health query")
    history: list[HistoryMessage] = Field(default_factory=list)
    selected_system: str = Field(default="Multisystem", description="Requested system: Multisystem, Ayurveda, Yoga, Unani, Siddha, or Homeopathy")
    lat: Optional[float] = Field(default=None, description="User latitude for hospital lookup")
    lng: Optional[float] = Field(default=None, description="User longitude for hospital lookup")


# ── Sub-response models ───────────────────────────────────────────────────────

class ExpertResponse(BaseModel):
    """Returned by each of the five AYUSH expert agents."""
    diagnosis: str = ""
    recommendations: str = ""
    herbs_or_remedies: list[str] = Field(default_factory=list)
    diet: str = ""
    lifestyle: str = ""
    evidence: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class YogaPoseImage(BaseModel):
    pose_name: str
    image_url: str
    source_url: str


class YogaResponse(BaseModel):
    """Returned by the Yoga expert + image search agents."""
    poses: list[str] = Field(default_factory=list)
    breathing_exercises: list[str] = Field(default_factory=list)
    lifestyle: str = ""
    images: list[YogaPoseImage] = Field(default_factory=list)


class HospitalInfo(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    distance_km: Optional[float] = None
    maps_url: Optional[str] = None


class HospitalReferral(BaseModel):
    """Returned when emergency is detected."""
    message: str
    hospitals: list[HospitalInfo] = Field(default_factory=list)
    nearest_hospital: Optional[HospitalInfo] = None
    emergency_number: str = "112"


class SourceDocument(BaseModel):
    """A cited source document chunk."""
    title: str
    page: Optional[int] = None
    domain: str
    excerpt: str


class ConsensusResponse(BaseModel):
    unified_recommendation: str = ""
    common_themes: list[str] = Field(default_factory=list)
    conflicts_detected: list[str] = Field(default_factory=list)
    ranked_advice: list[str] = Field(default_factory=list)


class ReviewerResponse(BaseModel):
    validated: bool = True
    warnings: list[str] = Field(default_factory=list)
    final_answer: str = ""
    patient_summary: str = ""


# ── Top-level response ────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    """
    Top-level response shape.  Every field maps directly to what the
    Next.js /chat page expects to render.
    """
    emergency: bool = False
    hospital_referral: Optional[HospitalReferral] = None
    patient_summary: str = ""
    ayurveda: Optional[ExpertResponse] = None
    siddha: Optional[ExpertResponse] = None
    unani: Optional[ExpertResponse] = None
    homeopathy: Optional[ExpertResponse] = None
    yoga: Optional[YogaResponse] = None
    consensus: Optional[ConsensusResponse] = None
    reviewer: Optional[ReviewerResponse] = None
    sources: list[SourceDocument] = Field(default_factory=list)

    class Config:
        json_encoders: dict[Any, Any] = {}
