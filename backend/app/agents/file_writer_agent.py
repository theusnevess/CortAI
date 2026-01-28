import json # Manipula objetos JSON
import uuid # Gera IDs únicos
from datetime import datetime # Trabalha com datas e horas
from pathlib import Path # Manipula caminhos de arquivos e diretórios

# Define caminhos para os arquivos de log e diretório de saída
DECISION_LOG_PATH = Path("storage/decision_log.jsonl")
OUTCOME_LOG_PATH = Path("storage/outcome_log.jsonl")
AGENT_OUTPUT_DIR = Path("storage/agent_output")


def read_last_decision():
    """
    Lê o último objeto Decision do arquivo de log decision_log.jsonl.
    Returs
        dict: O último objeto Decision.
    """
    with DECISION_LOG_PATH.open("r", encoding="utf-8") as f:
        last_line = None
        for line in f:
            if line.strip():
                last_line = line
        if last_line is None:
            raise RuntimeError("No decisions found in the log.")
        return json.loads(last_line)


def write_file_from_decision(decision):
    """
    Cria um arquivo de texto baseado no objeto Decision.
    Args:   
        decision (dict): O objeto Decision.
    Returns:                
        filepath (Path): O caminho do arquivo criado.
    """

    # Garante que o diretório de saída exista
    AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = AGENT_OUTPUT_DIR / f"{decision['decision_id']}.txt"

    # Conteúdo do arquivo baseado na decisão
    content = [
        f"process_id: {decision.get('process_id')}",
        f"decision_id: {decision.get('decision_id')}",
        f"decision_type: {decision.get('decision_type')}",
        f"rationale: {decision.get('rationale')}",
        f"execution_timestamp: {datetime.utcnow().isoformat()}",
    ]

    # Escreve o conteúdo no arquivo
    with file_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(content))

    return file_path


def build_outcome(decision, file_path):
    """
    Constrói um objeto Outcome baseado na decisão e no arquivo criado.
    Args:   
        decision (dict): O objeto Decision.
        file_path (Path): O caminho do arquivo criado.
    Returns:                
        dict: O objeto Outcome.  
    """

    # Constrói o objeto Outcome
    return {
        "outcome_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": decision["process_id"],
        "source_decision_id": decision["decision_id"],
        "execution_status": "success",
        "metrics": {
            "file_created": True,
            "path": str(file_path),
        },
    }


def append_outcome(outcome):
    """
    Adiciona um Outcome ao arquivo de log outcome_log.jsonl.
    Args:
        outcome (dict): O objeto Outcome a ser adicionado.
    """
    
    OUTCOME_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOME_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(outcome) + "\n")


def main():
    """
    Função principal que executa o agente de escrita de arquivos.
    1. Lê a última decisão do log.  
    2. Cria um arquivo baseado na decisão.
    3. Constrói um objeto Outcome.  
    4. Adiciona o Outcome ao log.
    """
    decision = read_last_decision()
    file_path = write_file_from_decision(decision)
    outcome = build_outcome(decision, file_path)
    append_outcome(outcome)


if __name__ == "__main__":
    main()
