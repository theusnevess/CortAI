# agents/file_writer_agent.py

import json
import uuid
from datetime import datetime
from pathlib import Path

DECISION_LOG_PATH = Path("storage/decision_log.jsonl")
OUTCOME_LOG_PATH = Path("storage/outcome_log.jsonl")
AGENT_OUTPUT_DIR = Path("storage/agent_output")


def read_last_decision():
    with DECISION_LOG_PATH.open("r", encoding="utf-8") as f:
        last_line = None
        for line in f:
            if line.strip():
                last_line = line
        if last_line is None:
            raise RuntimeError("No Decision found in decision_log.jsonl")
        return json.loads(last_line)


def write_file_from_decision(decision):
    AGENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = AGENT_OUTPUT_DIR / f"{decision['decision_id']}.txt"

    content = [
        f"process_id: {decision.get('process_id')}",
        f"decision_id: {decision.get('decision_id')}",
        f"decision_type: {decision.get('decision_type')}",
        f"rationale: {decision.get('rationale')}",
        f"execution_timestamp: {datetime.utcnow().isoformat()}",
    ]

    with file_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(content))

    return file_path


def build_outcome(decision, file_path):
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
    OUTCOME_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOME_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(outcome) + "\n")


def main():
    decision = read_last_decision()
    file_path = write_file_from_decision(decision)
    outcome = build_outcome(decision, file_path)
    append_outcome(outcome)


if __name__ == "__main__":
    main()
