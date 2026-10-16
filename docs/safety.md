# Safety case

> **SYNTHETIC DATA ONLY — NOT MEDICAL ADVICE — NOT FOR CLINICAL USE.**

## Invariants (documented here, enforced in code, covered by tests)

1. **No autonomous clinical decisions.**
   - `triage_referral()` returns a *routing suggestion* (priority + queue).
   - `assemble_packet()` returns a *draft bundle* for a human submitter.
   - `plan_discharge()` returns a *checklist draft*.
   - `ReviewQueue.is_final()` returns `False` until a clinician records
     a decision. Tested end-to-end: nothing downstream treats an
     unreviewed output as final.

2. **Clinician rationale is mandatory.** `clinician_decide()` raises
   unless a non-empty rationale is supplied. No silent rubber-stamping,
   no double decisions.

3. **Deterministic rules, cited.** Triage escalations cite rule IDs
   (`RED-FLAG-01`, `VITALS-02`, …); a routine decision cites
   `ROUTINE-01`. Thresholds and weights are demo values, stated as such
   in code comments — they are not clinical guidance.

4. **No approval authority.** The prior-auth module has no
   approve/deny API. Packets are assembled; payers and clinicians
   decide.

5. **Synthetic data by construction.** `SyntheticPatient` rejects
   `synthetic=False`. Age bands instead of exact ages. Seeded
   generation. `(SYNTHETIC)` markers on medications and codes.

## What real deployment would additionally require

- Clinical validation of every rule and threshold against real
  (de-identified) data with clinician oversight.
- HIPAA-compliant infrastructure: encryption, access controls, audit
  logging beyond this demo ledger, BAAs.
- Regulatory review appropriate to the jurisdiction and use case.
- Human-factors review of the clinician UI to prevent automation bias.

This project provides none of the above. It is a technical demonstration
of healthcare *operations* patterns.
