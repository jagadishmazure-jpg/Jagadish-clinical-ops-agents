"""Prior-authorization packet assembly.

Assembles the artifact bundle a human submitter needs for a prior-auth
request and scores its completeness. This module NEVER approves or
denies anything — approval is a payer/clinician decision. Packets are
assembled for human submitters, full stop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Required artifact slots for a complete packet (demo schema).
REQUIRED_ARTIFACTS = [
    "diagnosis_codes",
    "procedure_codes",
    "clinical_notes",
    "prior_treatments_tried",
    "imaging_or_labs",
    "referring_provider_npi",
]


@dataclass
class AuthPacket:
    packet_id: str
    referral_id: str
    artifacts: Dict[str, str] = field(default_factory=dict)
    synthetic: bool = True

    def missing(self) -> List[str]:
        return [a for a in REQUIRED_ARTIFACTS if not self.artifacts.get(a)]


@dataclass
class PacketReport:
    packet_id: str
    completeness_pct: float
    missing: List[str]
    present: List[str]
    submittable: bool
    note: str = (
        "Packet assembled for human submitter. "
        "This system does not approve or deny authorizations."
    )


def assemble_packet(
    packet_id: str,
    referral_id: str,
    artifacts: Dict[str, str],
) -> AuthPacket:
    """Bundle supplied artifacts into a packet. Unknown keys are kept
    but do not count toward required slots."""
    return AuthPacket(
        packet_id=packet_id, referral_id=referral_id, artifacts=dict(artifacts)
    )


def packet_completeness(packet: AuthPacket) -> PacketReport:
    """Score completeness and list exactly what is missing."""
    missing = packet.missing()
    present = [a for a in REQUIRED_ARTIFACTS if a not in missing]
    pct = round(100.0 * len(present) / len(REQUIRED_ARTIFACTS), 1)
    return PacketReport(
        packet_id=packet.packet_id,
        completeness_pct=pct,
        missing=missing,
        present=present,
        submittable=not missing,
    )
