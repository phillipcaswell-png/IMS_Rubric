# ATHENA Pillar Evidence Link Audit Draft
Status: DRAFT — Not Ratified
Authority: Audit Definition Only
Runtime Effect: None
Database Mutation: Not Authorized
Evidence Relinking: Not Authorized
Pillar Score Changes: Not Authorized

## 1. Purpose
Athena requires a formal pillar evidence link audit design before any evidence-to-pillar repair is considered.

The future audit exists to determine whether existing pillar judgments are:

- properly evidence-linked
- assessment-only placeholders
- historical preserved judgments
- reusable governed judgments
- candidates for future repair
- not repairable without re-evaluation

This document defines a future audit. It does not perform the audit, does not authorize running the audit, and does not authorize repair.

## 2. Source Authority
Source authority documents:

- ATHENA_DATA_HYGIENE_REPORT_DRAFT.md
- governance/design/ATHENA_DATA_CLEANUP_AUTHORITY_DRAFT.md

This audit draft is derived from Class F — Evidence / Pillar Link Audit in the cleanup authority draft.

Class G — Evidence / Pillar Link Repair remains unauthorized.

## 3. Operating Rules
No relinking before audit.
No repair before authority.
No backfill from inference alone.
No pillar score rewrite by audit.
No retroactive improvement of historical decision quality.
No evidence reuse without provenance.
No Microsoft HRV-002 ratification by audit.
No successor creation by audit.
Audit findings are not execution authority.
This draft is not standing approval to run the audit.

## 4. Audit Scope
The future audit applies first to:

- thesis_id=14 Microsoft source-context record
- thesis_id=1 NVIDIA Investment Thesis, Preserve — Substantive, Unsigned
- thesis_id=6 Meta Platforms, Preserve — Substantive, Unsigned
- thesis_id=7 Kodak Archived Constitutional Asset

Reason:
These records contain pillar_scores and evidence_items where missing or incomplete pillar_evidence_links may affect constitutional traceability.

The audit does not initially apply to:

- thesis_id=8, because it has no pillar_scores/evidence_items in the inspected hygiene report and is already an archived no-touch reference.
- thesis_id=9/10/11/12, because they are pipeline residue with extracted observations but no governed evidence_items or pillar_scores.
- thesis_id=3/4/5/13, because they are scratch/test candidates with no substantive linked data.
- thesis_id=2, because it is an orphan reference issue, not a pillar-link audit target.

## 5. Audit Questions
The future audit must answer for each scoped thesis:

1. Which pillar_scores exist?
2. Which pillar_scores have pillar_evidence_links?
3. Which pillar_scores have no pillar_evidence_links?
4. Which evidence_items are promoted?
5. Which evidence_items are unlinked?
6. Which evidence_items have related_pillar values but no formal pillar_evidence_links?
7. Which pillar judgments appear assessment-only?
8. Which pillar judgments are historical-only and should not be reused?
9. Which pillar judgments could become reusable only after explicit evidence-link repair authority?
10. Which records require re-evaluation rather than backfill?
11. Which links, if any, appear mechanically recoverable but still require explicit authority before repair?
12. Which gaps should be surfaced to the Independent Audit Contract as constitutional findings?

## 6. Required Audit Evidence
The future audit must use direct read-only SQLite inspection.

Minimum tables to inspect:

- theses
- pillar_scores
- pillar_evidence_links
- evidence_items
- evidence_staging
- evidence_observations
- decision_logs
- thesis_reviews
- thesis_events

The audit must not rely on UI labels alone.

The audit must report the exact SQL queries used.

The audit must use read-only database access.

## 7. Required Per-Thesis Output
For each scoped thesis_id, the future audit must produce:

- thesis identity and current classification
- pillar_scores count
- pillar_evidence_links count
- evidence_items count
- promoted evidence_items count
- unlinked promoted evidence_items count
- pillar_scores without links
- evidence_items without links
- related_pillar-only mappings
- assessment-only indicators
- decision_logs and thesis_reviews context
- whether the thesis can support reusable governed judgment without repair
- whether the thesis should remain historical-only pending repair/re-evaluation
- recommended authority class before any future action

## 8. Classification Outcomes
The future audit may classify each pillar judgment into one of these audit outcomes:

### Evidence-Linked Governed Judgment
Definition:
A pillar_score has explicit pillar_evidence_links to governed evidence_items.

Meaning:
Judgment may be reusable if all other governance criteria are satisfied.

### Assessment-Only Judgment
Definition:
A pillar_score exists without pillar_evidence_links and appears based on analyst narrative or non-linked assessment fields.

Meaning:
Judgment may be preserved historically but should not be treated as fully evidence-linked.

### Historical-Only Preserved Judgment
Definition:
A judgment belongs to a source-context, archived, or unsigned record and should remain preserved but not reused as active governed work.

Meaning:
No repair implied.

### Candidate for Future Link Repair
Definition:
A pillar_score lacks formal pillar_evidence_links, but there are promoted evidence_items with clear provenance that may support later repair.

Meaning:
Future repair may be proposed, but only after separate Class G authority.

### Requires Re-Evaluation
Definition:
The existing score cannot be safely linked to evidence without reconstructing judgment.

Meaning:
Do not backfill. Re-evaluate under future governed workflow if needed.

### Out of Scope
Definition:
No pillar_scores or governed evidence_items exist, or the record belongs to orphan/scratch/pipeline-residue categories.

Meaning:
Do not audit for repair.

## 9. Explicit Non-Authority
This draft does not authorize:

- DB mutation
- audit execution
- evidence relinking
- pillar_evidence_links backfill
- pillar score modification
- evidence item modification
- decision log modification
- thesis review modification
- Microsoft HRV-002 ratification
- HRV-002 successor creation
- evidence ingestion
- evidence migration
- Hermes startup
- SpaceX setup
- cleanup execution
- commit of audit findings as ratified authority

## 10. Future Audit Execution Requirements
Before a future audit is executed, the operator must receive explicit instruction to run it.

A future audit execution sprint must:

1. Confirm runtime DB authority.
2. Confirm read-only DB access.
3. Run git status --short before inspection.
4. Discover schema before querying.
5. Use SELECT-only queries.
6. Inspect thesis_id 14 first, then 1, 6, 7.
7. Return all SQL used.
8. Return per-thesis findings.
9. Return no-mutation confirmation.
10. Do not stage or commit without explicit instruction.

## 11. Relationship to Independent Audit Contract
Pillar-score-without-link findings are constitutional audit issues, not merely data hygiene issues.

The Independent Audit Contract should eventually be able to flag:

- pillar judgments without evidence links
- promoted evidence without pillar linkage
- assessment-only decisions
- reused historical judgments without authority
- attempted repair without Class G authority

## 12. Recommended Next Action
1. Review this audit-design draft.
2. If acceptable, commit this draft as a governance design artifact.
3. Then, only after explicit instruction, run a separate read-only audit sprint to produce actual findings.
4. Do not repair links until Class G authority exists.

This section recommends a future separate audit sprint. It does not authorize executing that audit, repairing links, or treating this draft as standing approval.

## 13. No-Mutation Guarantee
This draft defines audit scope only.
No DB mutation was performed.
No audit execution was performed.
No evidence was relinked.
No pillar_evidence_links rows were inserted, updated, deleted, or backfilled.
No pillar_scores were changed.
No evidence_items were changed.
No HRV-002 action was taken.
No Hermes or SpaceX work was started.
No files were staged.
No commits were made.
