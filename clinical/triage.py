"""Referral triage: deterministic rules, every decision cites its rule.

This is NOT a diagnosis engine. It is an ops-routing tool: incomplete
referrals bounce back for more information, red-flag keywords and vital
thresholds escalate priority, everything else routes to the requested
specialty queue. A clinician always reviews (see review.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .patients import Referral

# Deterministic red-flag keywords -> escalation rule. These are ops
# routing signals, not clinical judgments.
RED_FLAGS = {
    "chest pain": "RED-FLAG-01",
    "shortness of breath": "RED-FLAG-02",
    "uncontrolled bleeding": "RED-FLAG-03",
    "stroke symptoms": "RED-FLAG-04",
    "severe headache": "RED-FLAG-05",
}

# Vital thresholds that escalate priority (demo values, not clinical guidance).
VITAL_THRESHOLDS = {
    "systolic_bp": (">180", lambda v: v > 180, "VITALS-01"),
    "heart_rate": (">120", lambda v: v > 120, "VITALS-02"),
    "spo2": ("<90", lambda v: v < 90, "VITALS-03"),
}

PRIORITIES = ("routine", "urgent", "stat")


@dataclass
class TriageDecision:
    referral_id: str
    priority: str
    queue: str
    needs_info: List[str] = field(default_factory=list)
    rules_triggered: List[str] = field(default_factory=list)
    rationale: str = ""

    @property
    def is_complete(self) -> bool:
        return not self.needs_info


def triage_referral(referral: Referral) -> TriageDecision:
    """Route a referral. Deterministic; cites every triggering rule."""
    needs_info: List[str] = []
    rules: List[str] = []

    # Completeness gate first — never triage what we can't see.
    if not referral.clinical_notes or not referral.clinical_notes.strip():
        needs_info.append("clinical_notes")
        rules.append("COMPLETENESS-01: clinical notes missing")
    if not referral.vitals:
        needs_info.append("vitals")
        rules.append("COMPLETENESS-02: vitals missing")
    if not referral.specialty:
        needs_info.append("specialty")
        rules.append("COMPLETENESS-03: specialty missing")

    priority = "routine"
    notes_lower = (referral.clinical_notes or "").lower()

    for keyword, rule_id in RED_FLAGS.items():
        if keyword in notes_lower:
            priority = "urgent"
            rules.append(f"{rule_id}: red-flag keyword '{keyword}'")

    for vital_name, (desc, check, rule_id) in VITAL_THRESHOLDS.items():
        value = referral.vitals.get(vital_name)
        if value is not None and check(value):
            priority = "urgent"
            rules.append(f"{rule_id}: {vital_name} {value} {desc}")

    if referral.urgency_in == "urgent":
        priority = "urgent"
        rules.append("REFERRAL-01: referring clinician marked urgent")

    # Escalate to stat only on multiple independent urgent signals.
    urgent_signals = sum(1 for r in rules if r.startswith(("RED-FLAG", "VITALS")))
    if urgent_signals >= 2:
        priority = "stat"
        rules.append("ESCALATION-01: >=2 independent urgent signals -> stat")

    # Every decision cites at least one rule — the audit trail is never empty.
    if not rules and not needs_info:
        rules.append("ROUTINE-01: no red flags, vitals in range, complete -> routine")

    queue = referral.specialty or "unassigned"
    rationale = (
        f"priority={priority}; queue={queue}; "
        f"{len(rules)} rule(s) triggered"
        + ("; incomplete: " + ", ".join(needs_info) if needs_info else "")
    )
    return TriageDecision(
        referral_id=referral.referral_id,
        priority=priority,
        queue=queue,
        needs_info=needs_info,
        rules_triggered=rules,
        rationale=rationale,
    )
