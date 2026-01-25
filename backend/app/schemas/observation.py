from typing import Any, Dict
from pydantic import BaseModel


class Observation(BaseModel):
    observation_id: str
    timestamp: str
    process_id: str
    source_outcome_id: str
    facts: Dict[str, Any]
 