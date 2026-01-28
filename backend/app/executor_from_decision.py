# executor_from_decision.py

import json
import uuid
from datetime import datetime
from pathlib import Path

# Define caminhos para os arquivos de log
DECISION_LOG_PATH = Path("storage/decision_log.jsonl")
OUTCOME_LOG_PATH = Path("storage/outcome_log.jsonl")


def read_last_decision():
    """
    Lê a última decisão do arquivo de log de decisões.
    Returns: 
        dict: A última decisão registrada.
    Raises: 
        RuntimeError: Se nenhum decisão for encontrada no arquivo.
    """
    with DECISION_LOG_PATH.open("r", encoding="utf-8") as f:
        last_line = None
        for line in f:
            if line.strip():
                last_line = line
        if last_line is None:
            raise RuntimeError("No Decision found in decision_log.jsonl")
        return json.loads(last_line)


def execute_decision(decision):
    """
    Executa a decisão fornecida.
    Args:
        decision (dict): A decisão a ser executada.
    Returns:
        dict: O resultado da execução da decisão.
    """
    return {
        "outcome_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": decision["process_id"],
        "source_decision_id": decision["decision_id"],
        "execution_status": "executed",
        "metrics": {},
    }


def append_outcome(outcome):
    """
    Anexa o resultado da execução ao arquivo de log de resultados.
    Args:
        outcome (dict): O resultado da execução a ser registrado.
    """
    OUTCOME_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOME_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(outcome) + "\n")


def main():
    """
    Executa o fluxo principal: lê a última decisão, executa-a e registra o resultado.
    """
    decision = read_last_decision()
    outcome = execute_decision(decision)
    append_outcome(outcome)


if __name__ == "__main__":
    main()
