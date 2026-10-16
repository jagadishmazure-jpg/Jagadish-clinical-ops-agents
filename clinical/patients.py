"""Synthetic patient and referral data — fictional, for technical demos only.

Every record produced here is generated from a seed and carries an
explicit synthetic marker. No real patient data, no real PHI, no
medical advice. Not for clinical use.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List

SYNTHETIC_MARKER = "SYNTHETIC-DEMO-DATA"

# Age bands instead of exact ages — reduces re-identification surface even
# for synthetic data, and matches how ops dashboards bucket patients.
AGE_BANDS = ["18-39", "40-64", "65-79", "80+"]

CONDITIONS = [
    "hypertension", "type-2-diabetes", "asthma", "copd", "ckd-stage-3",
    "atrial-fibrillation", "depression", "osteoarthritis", "hyperlipidemia",
    "heart-failure",
]

SPECIALTIES = [
    "cardiology", "orthopedics", "neurology", "pulmonology",
    "endocrinology", "dermatology",
]

NOTE_SNIPPETS = [
    "Patient reports persistent symptoms over the past several weeks.",
    "Referred for specialist evaluation following primary care visit.",
    "Symptoms worsening despite conservative management.",
    "Routine follow-up requested; no acute distress noted.",
    "Family history noted; requesting specialist opinion.",
]


@dataclass
class SyntheticPatient:
    """A fictional patient record. Never contains real PHI."""

    patient_id: str
    age_band: str
    conditions: List[str] = field(default_factory=list)
    prior_admissions_12mo: int = 0
    synthetic: bool = True

    def __post_init__(self) -> None:
        if not self.synthetic:
            raise ValueError("SyntheticPatient must always be synthetic")


@dataclass
class Referral:
    """A fictional specialist referral."""

    referral_id: str
    patient: SyntheticPatient
    specialty: str
    urgency_in: str  # referring clinician's stated urgency
    clinical_notes: str
    vitals: dict = field(default_factory=dict)
    synthetic: bool = True


def gen_patient(rng: random.Random, idx: int) -> SyntheticPatient:
    n_conditions = rng.randint(0, 3)
    return SyntheticPatient(
        patient_id=f"PT-{idx:04d}",
        age_band=rng.choice(AGE_BANDS),
        conditions=rng.sample(CONDITIONS, n_conditions),
        prior_admissions_12mo=rng.randint(0, 2),
    )


def gen_referrals(n: int, seed: int = 42) -> List[Referral]:
    """Deterministic synthetic referral generator."""
    rng = random.Random(seed)
    referrals = []
    for i in range(n):
        patient = gen_patient(rng, i + 1)
        vitals: dict = {}
        if rng.random() < 0.8:  # most referrals carry vitals
            vitals = {
                "systolic_bp": rng.randint(100, 190),
                "heart_rate": rng.randint(55, 130),
                "spo2": rng.randint(88, 100),
            }
        referrals.append(
            Referral(
                referral_id=f"REF-{i + 1:04d}",
                patient=patient,
                specialty=rng.choice(SPECIALTIES),
                urgency_in=rng.choice(["routine", "urgent", "routine", "routine"]),
                clinical_notes=rng.choice(NOTE_SNIPPETS),
                vitals=vitals,
            )
        )
    return referrals
