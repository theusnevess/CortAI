from typing import Any, Dict
from pydantic import BaseModel


class Observation(BaseModel):
    """
    Esquema de dados para uma observação.
    Args:   
        observation_id (str): O ID único da observação.
        timestamp (str): O carimbo de data/hora da observação.
        process_id (str): O ID do processo associado.
        source_outcome_id (str): O ID do resultado de origem.
        facts (Dict[str, Any]): Um dicionário contendo os fatos observados.
    """
    observation_id: str
    timestamp: str
    process_id: str
    source_outcome_id: str
    facts: Dict[str, Any]
 