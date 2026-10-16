"""Hash-chained clinical ledger: every triage, packet, plan, and
clinician decision recorded, tamper-evident."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


def _canonical(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass
class LedgerEntry:
    seq: int
    event_type: str
    payload: Dict[str, Any]
    timestamp: str
    prev_hash: str
    entry_hash: str


@dataclass
class ClinicalLedger:
    entries: List[LedgerEntry] = field(default_factory=list)

    def record(self, event_type: str, payload: Dict[str, Any]) -> LedgerEntry:
        prev_hash = self.entries[-1].entry_hash if self.entries else "GENESIS"
        timestamp = datetime.now(timezone.utc).isoformat()
        seq = len(self.entries)
        body = _canonical(
            {"seq": seq, "event_type": event_type,
             "payload": payload, "timestamp": timestamp,
             "prev_hash": prev_hash}
        )
        entry_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        entry = LedgerEntry(seq, event_type, dict(payload), timestamp,
                            prev_hash, entry_hash)
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        prev = "GENESIS"
        for e in self.entries:
            body = _canonical(
                {"seq": e.seq, "event_type": e.event_type,
                 "payload": e.payload, "timestamp": e.timestamp,
                 "prev_hash": e.prev_hash}
            )
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != e.entry_hash:
                return False
            if e.prev_hash != prev:
                return False
            prev = e.entry_hash
        return True
