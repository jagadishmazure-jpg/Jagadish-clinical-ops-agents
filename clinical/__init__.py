"""clinical: end-to-end healthcare operations agents (synthetic demo).

Referral triage -> prior-auth packet assembly -> discharge planning,
with a clinician review queue and a hash-chained audit ledger.

SYNTHETIC DATA ONLY. Not medical advice. Not for clinical use.
"""

from .audit import ClinicalLedger, LedgerEntry
from .discharge import DischargePlan, plan_discharge
from .patients import Referral, SyntheticPatient, gen_referrals
from .priorauth import AuthPacket, PacketReport, assemble_packet, packet_completeness
from .review import ReviewItem, ReviewQueue
from .triage import TriageDecision, triage_referral

__all__ = [
    "ClinicalLedger",
    "LedgerEntry",
    "DischargePlan",
    "plan_discharge",
    "Referral",
    "SyntheticPatient",
    "gen_referrals",
    "AuthPacket",
    "PacketReport",
    "assemble_packet",
    "packet_completeness",
    "ReviewItem",
    "ReviewQueue",
    "TriageDecision",
    "triage_referral",
]
