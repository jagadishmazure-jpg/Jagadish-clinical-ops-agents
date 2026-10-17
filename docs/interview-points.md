# Interview points

Short, honest talking points for Jagadish-clinical-ops-agents. Every number quoted is from the
real run shown in the README.

- I automated the paperwork around care, not the care: every output is a draft and a clinician decides.
- Safety is in the API shape: the prior-auth module cannot approve or deny, and decisions need a rationale.
- Real run on 30 synthetic referrals: 13 routine, 14 urgent, 3 stat, 1 returned for missing information, with rule IDs cited.
- Synthetic by construction: the patient type refuses to be non-synthetic.

## Likely follow-up questions

- How would you validate the triage rules? (Retrospective review with clinicians on de-identified referrals.)
- Where would an LLM help? (Summarising notes into the packet, never deciding priority.)
- How do you keep PHI out of logs? (Log identifiers and rule IDs only; redact at the logger.)
