import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class RunLogger:
    def __init__(self, log_dir: str = "artifacts"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.events_path = os.path.join(self.log_dir, "events.jsonl")

    def log(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload or {},
        }
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def path(self) -> str:
        return self.events_path
