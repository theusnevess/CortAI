from typing import List, Union # Importa as classes List e Union do módulo typing
from pydantic import BaseModel # Importa a classe BaseModel do módulo pydantic

# Define a classe SegmentInput que herda de BaseModel
class SegmentInput(BaseModel):
    segment_id: Union[int, str]
    start_time: float
    end_time: float

# Define a classe TranscriptionOutput que herda de BaseModel
class TranscriptionOutput(BaseModel):
    segment_id: Union[int, str]
    start_time: float
    end_time: float
    text: str
