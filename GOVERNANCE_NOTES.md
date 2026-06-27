`related_pillar` on `evidence_items` is now metadata only. `pillar_evidence_links` is the authoritative source for evidence-to-pillar relationships. Migration of Evidence Coverage and the Decision Engine to consume `pillar_evidence_links` is a future governed milestone.

Mnemosyne operates in observation mode. Pattern detection informs analysts but does not modify framework, thesis, or decision records. Framework evolution remains a governed human activity supported—not directed—by historical observations.

MNEMOSYNE_MINIMUM_REVIEW_VOLUME = 10 is a constitutional threshold. It may only be changed through a governed documentation update.

Theia v1 — Evidence Staging Boundary:
Candidate evidence is not system evidence.
Staged evidence is not decision evidence.
Only analyst-confirmed evidence may support scores, thesis records,
or decision records. Promotion from evidence_staging to evidence_items
requires explicit analyst confirmation. Rejected evidence must include
a documented rejection_reason for audit trail completeness.

Agent Boundary Reference:
Theia: Acquire, Normalize, Classify, Stage. Never decides.
Themis: Validate, Govern, Gate. Never discovers evidence.
Analyst: Exercises judgment.
Evidence Repository: Official evidence only.
Mnemosyne: Observe, Calibrate, Learn. Never changes history.
