"""
Day 18 - Session 2: Integration & Safety
Cryptographic Audit Logger: Maintains an immutable, SHA-256 hash-chained audit log for all actions.
"""

import os
import sys
import json
import time
import hashlib
from typing import Dict, Any, List, Tuple


class CryptographicAuditLogger:
    """Tamper-evident audit log chaining each transaction with SHA-256 hashes."""

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, log_path: str):
        self.log_path = log_path
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write("")  # Create empty file

    def get_latest_hash(self) -> str:
        """Retrieves the entry hash of the last entry in the log, or GENESIS_HASH."""
        if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
            return self.GENESIS_HASH

        last_line = ""
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()

        if not last_line:
            return self.GENESIS_HASH

        try:
            entry = json.loads(last_line)
            return entry.get("entry_hash", self.GENESIS_HASH)
        except Exception:
            return self.GENESIS_HASH

    def log_event(self, incident_id: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Appends a cryptographically chained event to the audit log."""
        prev_hash = self.get_latest_hash()
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Construct raw payload for hashing
        payload_str = json.dumps(details, sort_keys=True)
        raw_to_hash = f"{prev_hash}:{timestamp}:{incident_id}:{event_type}:{payload_str}".encode("utf-8")
        entry_hash = hashlib.sha256(raw_to_hash).hexdigest()

        event_record = {
            "timestamp": timestamp,
            "incident_id": incident_id,
            "event_type": event_type,
            "details": details,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_record) + "\n")

        return event_record

    def verify_chain_integrity(self) -> Tuple[bool, int, str]:
        """Verifies that all entries in the audit trail have valid hash linkages."""
        if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
            return True, 0, "Log file is empty (valid)."

        expected_prev = self.GENESIS_HASH
        count = 0

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                except Exception as e:
                    return False, count, f"Corrupted JSON on line {line_no}: {str(e)}"

                if entry.get("prev_hash") != expected_prev:
                    return False, count, f"Hash chain broken at entry #{line_no}: expected prev_hash {expected_prev}, got {entry.get('prev_hash')}"

                # Recompute hash
                payload_str = json.dumps(entry["details"], sort_keys=True)
                raw_to_hash = f"{entry['prev_hash']}:{entry['timestamp']}:{entry['incident_id']}:{entry['event_type']}:{payload_str}".encode("utf-8")
                recomputed_hash = hashlib.sha256(raw_to_hash).hexdigest()

                if recomputed_hash != entry["entry_hash"]:
                    return False, count, f"Tampered record at entry #{line_no}: hash mismatch!"

                expected_prev = entry["entry_hash"]
                count += 1

        return True, count, f"All {count} entries verified cryptographically."
