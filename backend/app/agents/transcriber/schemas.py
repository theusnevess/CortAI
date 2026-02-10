from pydantic import BaseModel


class SegmentInput(BaseModel):
    segment_id: str | int
    start_time: float
    end_time: float


class TranscriptionOutput(BaseModel):
    segment_id: str | int
    start_time: float
    end_time: float
    text: str
