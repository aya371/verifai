"""
Audit Log — Append-only hardened version.
Save to: backend/database/audit_log.py

Security: log file is opened in append mode only.
Old entries can never be overwritten or deleted through this module.
"""
import os
import json
from datetime import datetime
from backend.utils.logger import logger

LOG_PATH = os.path.join(
    os.path.dirname(__file__), "../../data/audit.log"
)

def log_event(event_type: str, data: dict, user_id: str = "anonymous") -> None:
    """
    Append a single audit event to the log file.
    File is always opened with 'a' (append) — never 'w' (write/overwrite).
    """
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event":     event_type,
            "user_id":   user_id,
            "data":      data,
        }
        # ✅ 'a' mode = append only, never truncates existing log
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        # Log failure should never crash the application
        logger.warning(f"Audit log write failed: {e}")

def read_recent(n: int = 100) -> list:
    """Read the last n entries from the audit log (for admin review)."""
    try:
        if not os.path.exists(LOG_PATH):
            return []
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        entries = []
        for line in lines[-n:]:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return entries
    except Exception as e:
        logger.warning(f"Audit log read failed: {e}")
        return []
