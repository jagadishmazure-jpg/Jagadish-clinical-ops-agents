"""Human-in-the-loop: the clinician review queue.

Core invariant (documented, tested): the system NEVER makes clinical
decisions autonomously. Triage decisions are routing suggestions,
packets are assembled drafts, discharge plans are checklists — every
one of them requires an explicit clinician decision recorded here
before it counts as final.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

REVIEWABLE_KINDS = ("triage", "packet", "discharge_plan")
DECISIONS = ("approved", "overridden", "rejected")


@dataclass
class ReviewItem:
    item_id: str
    kind: str
    reference_id: str  # referral_id / packet_id / plan_id
    payload_summary: str
    status: str = "pending"  # pending | decided
    decision: Optional[str] = None
    decided_by: Optional[str] = None
    rationale: Optional[str] = None
    decided_at: Optional[str] = None


@dataclass
class ReviewQueue:
    items: Dict[str, ReviewItem] = field(default_factory=dict)

    def submit(self, item: ReviewItem) -> ReviewItem:
        if item.kind not in REVIEWABLE_KINDS:
            raise ValueError(f"unknown review kind: {item.kind}")
        self.items[item.item_id] = item
        return item

    def pending(self) -> List[ReviewItem]:
        return [i for i in self.items.values() if i.status == "pending"]

    def clinician_decide(
        self,
        item_id: str,
        decision: str,
        decided_by: str,
        rationale: str,
    ) -> ReviewItem:
        """Record a clinician's decision. Rationale is mandatory —
        no silent rubber-stamping."""
        if decision not in DECISIONS:
            raise ValueError(f"unknown decision: {decision}")
        if not rationale or not rationale.strip():
            raise ValueError("clinician rationale is required")
        item = self.items[item_id]  # KeyError if unknown: fail loud
        if item.status != "pending":
            raise ValueError(f"item {item_id} already decided")
        item.status = "decided"
        item.decision = decision
        item.decided_by = decided_by
        item.rationale = rationale.strip()
        item.decided_at = datetime.now(timezone.utc).isoformat()
        return item

    def is_final(self, reference_id: str, kind: str) -> bool:
        """True only if a clinician has decided on this item."""
        return any(
            i.kind == kind and i.reference_id == reference_id and i.status == "decided"
            for i in self.items.values()
        )
