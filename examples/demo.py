"""Triage 30 synthetic referrals, assemble a prior-auth packet, draft a discharge plan (offline).

SYNTHETIC DATA ONLY. NOT MEDICAL ADVICE. Every output is a draft for a clinician.
"""
from collections import Counter

from clinical import (
    ReviewItem,
    ReviewQueue,
    assemble_packet,
    gen_referrals,
    packet_completeness,
    plan_discharge,
    triage_referral,
)

referrals = gen_referrals(30, seed=42)
decisions = [triage_referral(r) for r in referrals]
print("Triage of 30 synthetic referrals")
print("  priority:", dict(sorted(Counter(d.priority for d in decisions).items())))
print("  incomplete (sent back for info):", sum(not d.is_complete for d in decisions))
first_stat = next(d for d in decisions if d.priority == "stat")
print(f"  example {first_stat.referral_id}: {first_stat.priority} -> {first_stat.queue}")
for rule in first_stat.rules_triggered:
    print("     rule:", rule)

queue = ReviewQueue()
queue.submit(ReviewItem("RV-1", "triage", first_stat.referral_id, first_stat.rationale))
print(f"  final before clinician decides? {queue.is_final(first_stat.referral_id, 'triage')}")
queue.clinician_decide("RV-1", "approved", "dr.example", "agree with routing")
print(f"  final after clinician decides?  {queue.is_final(first_stat.referral_id, 'triage')}")

packet = assemble_packet("PA-1", referrals[0].referral_id,
                         {"diagnosis_codes": "Z00.00 (SYNTHETIC)", "clinical_notes": referrals[0].clinical_notes})
report = packet_completeness(packet)
print(f"\nPrior-auth packet PA-1: {report.completeness_pct}% complete, submittable={report.submittable}")
print("  missing:", ", ".join(report.missing))
print("  note:", report.note)

patient = referrals[1].patient
plan = plan_discharge("DC-1", patient, [referrals[1].specialty])
print(f"\nDischarge draft DC-1 for {patient.patient_id} (age band {patient.age_band}):"
      f" risk {plan.risk_score} ({plan.risk_tier}), clinician_reviewed={plan.clinician_reviewed}")
print("  follow-ups:", plan.followups)
print("  risk factors:", plan.risk_factors)
