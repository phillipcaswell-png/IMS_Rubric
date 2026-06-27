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

Validation Case 001 Regression Requirement (effective v1.0.0):

Every architectural milestone from v1.0.0 forward must demonstrate
that Validation Case 001 (Meta Platforms 2012) can still be executed
correctly against the modified codebase before the milestone is
approved for commit.

Minimum regression criteria:
1. Evidence cutoff enforcement blocks post-2012-05-18 evidence
2. Themis gate enforces 11/11 pillar completeness before decision
3. Validation configuration locks after first decision record
4. Layer 1 decision record remains immutable
5. Layer 2 thesis reviews can be created independently
6. Mnemosyne outcome attribution records correctly

This regression is not a full re-execution of the validation case.
It is a constitutional smoke test against the five enforcement
mechanisms that v1.0.0 validated.

MVP-020 Athena Orchestration Principle:
Athena coordinates constitutional subsystems. It contributes organization, not judgment. Every section of the AthenaPreBrief has an owning subsystem. Athena contributes zero constitutional authority of its own.

get_athena_prebrief(thesis_id) is read-only. It may never write, enforce, score, decide, or mutate any governed record.

Athena Agent Authority Boundary:

Agents may:
- gather
- stage
- summarize
- surface
- classify (non-governed)
- suggest

Agents may not:
- decide
- enforce
- score
- promote
- review
- mutate governed records
- bypass constitutional gates

All governed actions require either an existing governed service or an authenticated analyst action.

Suggestions are advisory only. Recording governed actions remains the responsibility of the analyst and the appropriate constitutional subsystem.

Deferred Architectural Intentions:
- Canonical validation lock helper
- Subsystem summary services
- Validation Portfolio concept
