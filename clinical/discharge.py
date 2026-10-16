"""Discharge planning: checklist generation for clinician review.

Generates a structured discharge checklist — follow-ups, synthetic
medication reconciliation, home-care flags — plus a deterministic
readmission-risk factor score. The plan is a draft for clinician
review, never a clinical order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .patients import SyntheticPatient

# Synthetic medication names for reconciliation demos (fictional regimens).
SYNTHETIC_MEDS = {
    "hypertension": ["lisinopril 10mg daily (SYNTHETIC)"],
    "type-2-diabetes": ["metformin 500mg twice daily (SYNTHETIC)"],
    "atrial-fibrillation": ["apixaban 5mg twice daily (SYNTHETIC)"],
    "heart-failure": ["furosemide 40mg daily (SYNTHETIC)"],
    "asthma": ["albuterol inhaler as needed (SYNTHETIC)"],
    "copd": ["tiotropium inhaler daily (SYNTHETIC)"],
    "depression": ["sertraline 50mg daily (SYNTHETIC)"],
    "hyperlipidemia": ["atorvastatin 20mg nightly (SYNTHETIC)"],
}

SPECIALTY_FOLLOWUP_DAYS = {
    "cardiology": 7,
    "orthopedics": 14,
    "neurology": 14,
    "pulmonology": 10,
    "endocrinology": 30,
    "dermatology": 30,
}

# Deterministic risk-factor weights (demo values, not clinical guidance).
AGE_BAND_POINTS = {"18-39": 0, "40-64": 1, "65-79": 2, "80+": 3}


@dataclass
class DischargePlan:
    plan_id: str
    patient_id: str
    followups: List[Dict[str, str]] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    home_care_flags: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    risk_score: int = 0
    risk_tier: str = "low"
    clinician_reviewed: bool = False
    synthetic: bool = True


def _risk_score(patient: SyntheticPatient) -> tuple[int, List[str]]:
    factors: List[str] = []
    score = AGE_BAND_POINTS.get(patient.age_band, 0)
    if patient.age_band in ("65-79", "80+"):
        factors.append(f"age band {patient.age_band}")
    n_cond = len(patient.conditions)
    score += min(n_cond, 4)
    if n_cond:
        factors.append(f"{n_cond} chronic condition(s)")
    score += min(patient.prior_admissions_12mo * 2, 4)
    if patient.prior_admissions_12mo:
        factors.append(f"{patient.prior_admissions_12mo} admission(s) in 12mo")
    return score, factors


def plan_discharge(
    plan_id: str, patient: SyntheticPatient, specialties: List[str]
) -> DischargePlan:
    """Build a discharge checklist draft for clinician review."""
    followups = [
        {
            "specialty": spec,
            "within_days": str(SPECIALTY_FOLLOWUP_DAYS.get(spec, 14)),
        }
        for spec in specialties
    ]
    medications: List[str] = []
    for cond in patient.conditions:
        medications.extend(SYNTHETIC_MEDS.get(cond, []))

    home_care_flags: List[str] = []
    if patient.age_band == "80+":
        home_care_flags.append("consider home safety evaluation")
    if "heart-failure" in patient.conditions or "copd" in patient.conditions:
        home_care_flags.append("consider home health nursing visit")
    if patient.prior_admissions_12mo >= 2:
        home_care_flags.append("high utilizer: consider care coordinator")

    score, factors = _risk_score(patient)
    tier = "low" if score <= 2 else "medium" if score <= 5 else "high"

    return DischargePlan(
        plan_id=plan_id,
        patient_id=patient.patient_id,
        followups=followups,
        medications=medications,
        home_care_flags=home_care_flags,
        risk_factors=factors,
        risk_score=score,
        risk_tier=tier,
    )
