"""Tests for clinical ops agents. All synthetic, deterministic."""

import pytest

from clinical import (
    ClinicalLedger,
    ReviewItem,
    ReviewQueue,
    SyntheticPatient,
    assemble_packet,
    gen_referrals,
    packet_completeness,
    plan_discharge,
    triage_referral,
)
from clinical.patients import Referral


def _referral(**kw):
    base = dict(
        referral_id="REF-0001",
        patient=SyntheticPatient("PT-0001", "40-64", ["hypertension"], 0),
        specialty="cardiology",
        urgency_in="routine",
        clinical_notes="Referred for specialist evaluation following primary care visit.",
        vitals={"systolic_bp": 120, "heart_rate": 72, "spo2": 98},
    )
    base.update(kw)
    return Referral(**base)


# ---------- patients ----------

def test_gen_referrals_deterministic():
    a = gen_referrals(20, seed=7)
    b = gen_referrals(20, seed=7)
    assert [r.referral_id for r in a] == [r.referral_id for r in b]
    assert [r.patient.patient_id for r in a] == [r.patient.patient_id for r in b]


def test_all_records_marked_synthetic():
    for r in gen_referrals(10):
        assert r.synthetic and r.patient.synthetic


def test_patient_ids_formatted():
    refs = gen_referrals(5)
    assert refs[0].patient.patient_id == "PT-0001"
    assert refs[0].referral_id == "REF-0001"


def test_patient_rejects_non_synthetic():
    with pytest.raises(ValueError):
        SyntheticPatient("PT-1", "40-64", synthetic=False)


# ---------- triage ----------

def test_red_flag_keyword_escalates_with_cited_rule():
    r = _referral(clinical_notes="Patient reports chest pain radiating to arm.")
    d = triage_referral(r)
    assert d.priority == "urgent"
    assert any("RED-FLAG-01" in rule for rule in d.rules_triggered)


def test_vital_threshold_escalates_with_cited_rule():
    r = _referral(vitals={"systolic_bp": 190, "heart_rate": 72, "spo2": 98})
    d = triage_referral(r)
    assert d.priority == "urgent"
    assert any("VITALS-01" in rule for rule in d.rules_triggered)


def test_two_urgent_signals_escalate_to_stat():
    r = _referral(
        clinical_notes="shortness of breath at rest",
        vitals={"systolic_bp": 185, "heart_rate": 72, "spo2": 98},
    )
    d = triage_referral(r)
    assert d.priority == "stat"
    assert any("ESCALATION-01" in rule for rule in d.rules_triggered)


def test_incomplete_referral_lists_gaps():
    r = _referral(clinical_notes="   ", vitals={})
    d = triage_referral(r)
    assert not d.is_complete
    assert "clinical_notes" in d.needs_info
    assert "vitals" in d.needs_info
    assert any("COMPLETENESS" in rule for rule in d.rules_triggered)


def test_routine_referral_routes_to_specialty_queue():
    d = triage_referral(_referral())
    assert d.priority == "routine"
    assert d.queue == "cardiology"
    assert d.is_complete


def test_referring_clinician_urgent_honored():
    d = triage_referral(_referral(urgency_in="urgent"))
    assert d.priority == "urgent"
    assert any("REFERRAL-01" in rule for rule in d.rules_triggered)


def test_every_decision_cites_rules():
    d = triage_referral(_referral())
    assert d.rules_triggered  # even routine cites the rationale path
    assert d.rationale


# ---------- prior auth ----------

FULL_ARTIFACTS = {
    "diagnosis_codes": "I10 (SYNTHETIC)",
    "procedure_codes": "93000 (SYNTHETIC)",
    "clinical_notes": "notes (SYNTHETIC)",
    "prior_treatments_tried": "conservative mgmt (SYNTHETIC)",
    "imaging_or_labs": "ECG (SYNTHETIC)",
    "referring_provider_npi": "1234567890 (SYNTHETIC)",
}


def test_complete_packet_scores_100():
    p = assemble_packet("PKT-1", "REF-0001", FULL_ARTIFACTS)
    rep = packet_completeness(p)
    assert rep.completeness_pct == 100.0
    assert rep.missing == []
    assert rep.submittable


def test_missing_items_listed_exactly():
    partial = {k: v for k, v in FULL_ARTIFACTS.items() if k != "imaging_or_labs"}
    p = assemble_packet("PKT-2", "REF-0001", partial)
    rep = packet_completeness(p)
    assert rep.missing == ["imaging_or_labs"]
    assert not rep.submittable
    assert rep.completeness_pct < 100.0


def test_packet_never_auto_approves():
    # There is no approve/deny API on packets at all: the module only
    # assembles and scores. Assert the surface stays that way.
    p = assemble_packet("PKT-3", "REF-0001", FULL_ARTIFACTS)
    assert not hasattr(p, "approve")
    assert not hasattr(p, "deny")
    assert "does not approve" in packet_completeness(p).note


# ---------- discharge ----------

def test_discharge_checklist_complete():
    patient = SyntheticPatient("PT-0002", "65-79", ["hypertension", "heart-failure"], 1)
    plan = plan_discharge("PLAN-1", patient, ["cardiology"])
    assert plan.followups == [{"specialty": "cardiology", "within_days": "7"}]
    assert any("lisinopril" in m for m in plan.medications)
    assert plan.home_care_flags  # heart-failure -> home health flag


def test_risk_scoring_deterministic():
    low = SyntheticPatient("PT-1", "18-39", [], 0)
    high = SyntheticPatient("PT-2", "80+", ["hypertension", "heart-failure", "copd"], 2)
    assert plan_discharge("P1", low, []).risk_tier == "low"
    ph = plan_discharge("P2", high, [])
    assert ph.risk_tier == "high"
    assert ph.risk_factors  # every point cited


def test_plan_requires_clinician_review_flag():
    plan = plan_discharge("P3", SyntheticPatient("PT-3", "40-64", [], 0), [])
    assert plan.clinician_reviewed is False


# ---------- review / safety invariants ----------

def test_clinician_decision_requires_rationale():
    q = ReviewQueue()
    q.submit(ReviewItem("RV-1", "triage", "REF-0001", "urgent cardiology"))
    with pytest.raises(ValueError):
        q.clinician_decide("RV-1", "approved", "dr.smith", "   ")


def test_item_not_final_before_clinician_decides():
    q = ReviewQueue()
    q.submit(ReviewItem("RV-2", "packet", "PKT-1", "complete packet"))
    assert not q.is_final("PKT-1", "packet")
    q.clinician_decide("RV-2", "approved", "dr.smith", "packet complete")
    assert q.is_final("PKT-1", "packet")


def test_no_double_decision():
    q = ReviewQueue()
    q.submit(ReviewItem("RV-3", "triage", "REF-0001", "urgent"))
    q.clinician_decide("RV-3", "overridden", "dr.smith", "downgrade: stable")
    with pytest.raises(ValueError):
        q.clinician_decide("RV-3", "approved", "dr.jones", "second look")


def test_unknown_kind_rejected():
    q = ReviewQueue()
    with pytest.raises(ValueError):
        q.submit(ReviewItem("RV-4", "diagnosis", "REF-1", "x"))


# ---------- ledger ----------

def test_ledger_chain_verifies():
    ledger = ClinicalLedger()
    ledger.record("triage", {"referral_id": "REF-0001", "priority": "urgent"})
    ledger.record("clinician_decision", {"item": "RV-1", "decision": "approved"})
    assert ledger.verify_chain()
    assert ledger.entries[1].prev_hash == ledger.entries[0].entry_hash


def test_ledger_tamper_detected():
    ledger = ClinicalLedger()
    ledger.record("triage", {"referral_id": "REF-0001"})
    ledger.entries[0].payload["priority"] = "routine"  # tamper
    assert not ledger.verify_chain()


# ---------- end to end ----------
def test_end_to_end_referral_to_signoff():
    ledger = ClinicalLedger()
    queue = ReviewQueue()

    referral = _referral(clinical_notes="Patient reports chest pain on exertion.")
    triage = triage_referral(referral)
    ledger.record("triage", {"referral_id": referral.referral_id,
                             "priority": triage.priority,
                             "rules": triage.rules_triggered})
    assert triage.priority == "urgent"

    queue.submit(ReviewItem("RV-E2E-1", "triage", referral.referral_id,
                            triage.rationale))
    assert not queue.is_final(referral.referral_id, "triage")
    queue.clinician_decide("RV-E2E-1", "approved", "dr.smith",
                           "agree: red-flag keyword present")
    ledger.record("clinician_decision", {"item": "RV-E2E-1",
                                         "decision": "approved"})
    assert queue.is_final(referral.referral_id, "triage")

    packet = assemble_packet("PKT-E2E", referral.referral_id, FULL_ARTIFACTS)
    report = packet_completeness(packet)
    ledger.record("packet", {"packet_id": packet.packet_id,
                             "completeness": report.completeness_pct})
    assert report.submittable

    plan = plan_discharge("PLAN-E2E", referral.patient, [referral.specialty])
    ledger.record("discharge_plan", {"plan_id": plan.plan_id,
                                     "risk_tier": plan.risk_tier})

    assert ledger.verify_chain()
    # Nothing is final without the clinician: the invariant holds end to end.
    assert not queue.is_final(packet.packet_id, "packet")
    assert not queue.is_final(plan.plan_id, "discharge_plan")


# ---------- extra coverage ----------

def test_missing_specialty_routes_to_unassigned():
    d = triage_referral(_referral(specialty=""))
    assert d.queue == "unassigned"
    assert "specialty" in d.needs_info


def test_unknown_specialty_followup_defaults():
    plan = plan_discharge("P9", SyntheticPatient("PT-9", "40-64", [], 0), ["urology"])
    assert plan.followups == [{"specialty": "urology", "within_days": "14"}]


def test_pending_queue_lists_only_undecided():
    q = ReviewQueue()
    q.submit(ReviewItem("RV-A", "triage", "REF-1", "x"))
    q.submit(ReviewItem("RV-B", "packet", "PKT-1", "y"))
    q.clinician_decide("RV-A", "approved", "dr.smith", "ok")
    assert [i.item_id for i in q.pending()] == ["RV-B"]


def test_referral_generation_covers_specialties():
    refs = gen_referrals(60, seed=3)
    seen = {r.specialty for r in refs}
    assert len(seen) >= 3  # generator exercises multiple queues
