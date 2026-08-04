from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    agent: str
    label: str
    status: str
    duration_ms: int
    summary: str


class Detection(BaseModel):
    kind: str
    label: str
    bbox: list[int]
    confidence: float
    area_ratio: float
    length_estimate: float
    explanation: str = ""


class RecordSummary(BaseModel):
    id: int
    filename: str
    created_at: str
    risk_level: str
    review_status: str
    confidence: float
    detection_count: int
    original_url: str
    annotated_url: str
    crack_count: int = 0
    spalling_count: int = 0
    stain_count: int = 0


class DetectionRecord(RecordSummary):
    quality: dict
    detections: list[Detection]
    workflow: list[WorkflowStep]
    metrics: dict
    risk_reason: str
    review_note: str = ""


class ReviewRequest(BaseModel):
    status: str = Field(min_length=1, max_length=40)
    risk_level: str = Field(pattern="^(低|中|高)$")
    review_note: str = Field(default="", max_length=800)
