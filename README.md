# Clinical ops agents

> **SYNTHETIC DATA ONLY — NOT MEDICAL ADVICE — NOT FOR CLINICAL USE.**
> Every patient, referral, and record in this project is fictional,
> generated from a random seed for technical demonstration. Nothing here
> diagnoses, treats, or advises on any real condition.

End-to-end healthcare *operations* automation: the paperwork layer
around care delivery, not care itself.

## The ops problem

- **Referral backlogs.** Incoming referrals arrive incomplete or
  mis-routed; staff triage them by hand.
- **Prior-auth paperwork burden.** Submitters chase missing artifacts
  (codes, notes, prior treatments) across systems.
- **Discharge gaps.** Follow-ups, medication reconciliation, and
  home-care needs fall through cracks at discharge.

This project automates the *assembly and routing* of that work while
keeping every decision with a human clinician.

## What it does

```
referral ──▶ triage ──▶ clinician review ──▶ prior-auth packet ──▶ clinician sign-off
                                                        │
patient ──▶ discharge plan ──▶ clinician review ─────────┘
                    │
                    ▼
            hash-chained audit ledger (everything recorded)
```

| Stage | Module | What it produces |
|---|---|---|
| Referral triage | `clinical/triage.py` | Priority + specialty queue; every decision cites its rule |
| Packet assembly | `clinical/priorauth.py` | Completeness-scored artifact bundle for a human submitter |
| Discharge planning | `clinical/discharge.py` | Checklist draft + deterministic risk factors |
| Clinician review | `clinical/review.py` | The human decision, with mandatory rationale |
| Audit | `clinical/audit.py` | Tamper-evident ledger of every step |

## Example walkthrough

```python
from clinical import gen_referrals, triage_referral, ReviewQueue, ReviewItem

referral = gen_referrals(1, seed=42)[0]
decision = triage_referral(referral)
print(decision.priority)        # routine | urgent | stat
print(decision.rules_triggered) # every triggering rule, cited
print(decision.needs_info)      # [] when complete, else what's missing

queue = ReviewQueue()
queue.submit(ReviewItem("RV-1", "triage", referral.referral_id,
                        decision.rationale))
queue.clinician_decide("RV-1", "approved", "dr.smith",
                       "agree with routing")
# Nothing is final until the clinician decides. Ever.
```

## Safety invariants

1. **Deterministic rules only.** Triage uses keyword/vital rules, not ML
   diagnosis. Risk scores are weighted counts, not predictions.
2. **Humans decide.** Triage outputs are routing suggestions, packets are
   drafts, plans are checklists. `ReviewQueue.is_final()` is false until
   a clinician records a decision with rationale. The packet module has
   no approve/deny API at all.
3. **Synthetic data.** Age bands instead of ages, seeded fictional
   patients, `(SYNTHETIC)` markers on meds and codes.

See [docs/safety.md](docs/safety.md) for the full safety case.

## Production path

- **EHR integration** via FHIR (referrals in, orders out).
- **Clinician UI** for the review queue (inbox-style approve/override).
- **Terminology services** for real ICD/CPT coding (this demo uses
  placeholder codes).
- Real deployment additionally requires clinical validation, HIPAA
  controls, and regulatory review — none of which this demo provides.

## Tests

```bash
pytest -q   # 28 tests, deterministic, no network or keys
```
