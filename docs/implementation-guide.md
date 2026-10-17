# Implementation guide: from offline build to Azure

> Status: **planned**. Nothing here has been deployed. The offline build in this
> repository is what exists today; this guide is how it would be taken to a
> real Azure environment.

## Azure service mapping

| Offline component | Azure service (planned) | Notes |
|---|---|---|
| Synthetic referrals and patients | Azure Health Data Services (FHIR R4): ServiceRequest, Patient, Condition | Synthetic data only until validated |
| Triage and packet logic | Azure Functions or Container Apps with managed identity | No direct EHR writes |
| Review queue | Clinician inbox web app on App Service with Entra ID sign-in | Rationale required |
| Ledger | Azure immutable blob storage | Audit retention per policy |
| Monitoring | Azure Monitor with PHI-free logs | Log IDs, not content |

## Steps

1. Map synthetic referrals to FHIR ServiceRequest and Patient resources in a test FHIR service.
2. Run triage and packet assembly as functions that read FHIR and write only draft tasks.
3. Build the clinician inbox with Entra ID sign-in; decisions go back as FHIR Task updates.
4. Keep logs free of PHI; write the ledger to immutable storage.
5. Run a clinical validation of every rule with clinicians before any real data is used.

## Guardrails to keep when going live

- No autonomous clinical decisions: triage outputs are routing suggestions, packets and plans are drafts.
- `clinician_decide()` refuses an empty rationale and refuses to decide an item twice.
- The prior-auth module has no approval authority by design.
- `SyntheticPatient` raises if constructed as non-synthetic; patients carry age bands, not ages; codes and medicines are marked SYNTHETIC.
- Every event can be recorded on a hash-chained ledger and verified.

## What to measure before calling it production-ready

- Agreement between suggested and clinician-confirmed priority.
- Share of prior-auth packets complete on first submission.
- Follow-up completion rate after discharge.
