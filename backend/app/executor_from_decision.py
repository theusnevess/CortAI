# executor_from_decision.py

import json
import uuid
from datetime import datetime
from pathlib import Path

DECISION_LOG_PATH = Path("storage/decision_log.jsonl")
OUTCOME_LOG_PATH = Path("storage/outcome_log.jsonl")


def read_last_decision():
    with DECISION_LOG_PATH.open("r", encoding="utf-8") as f:
        last_line = None
        for line in f:
            if line.strip():
                last_line = line
        if last_line is None:
            raise RuntimeError("No Decision found in decision_log.jsonl")
        return json.loads(last_line)


def execute_decision(decision):
    return {
        "outcome_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "process_id": decision["process_id"],
        "source_decision_id": decision["decision_id"],
        "execution_status": "executed",
        "metrics": {},
    }


def append_outcome(outcome):
    OUTCOME_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOME_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(outcome) + "\n")


def main():
    decision = read_last_decision()
    outcome = execute_decision(decision)
    append_outcome(outcome)


if __name__ == "__main__":
    main()
