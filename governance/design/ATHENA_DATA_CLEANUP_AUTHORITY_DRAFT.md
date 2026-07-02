# ATHENA Data Cleanup Authority Draft
Status: DRAFT — Not Ratified
Authority: None until explicitly approved
Runtime Effect: None
Database Mutation: Not Authorized
Application Routing Changes: Not Authorized

## 1. Purpose
Athena requires explicit governance authority before changing, hiding, repairing, deleting, relinking, or reclassifying runtime records identified by the data hygiene report.

This document defines a proposed authority framework only.
It is not an executable cleanup action and does not authorize runtime mutation.

## 2. Source Report
Source report:
ATHENA_DATA_HYGIENE_REPORT_DRAFT.md

This cleanup authority draft depends on findings from the source report, which was produced from read-only inspection.

## 3. Operating Rules
No cleanup before visibility.
No mutation before authority.
No deletion before preservation.
No repair before classification.
No relinking before evidence-link audit.
No ratification by implication.
Preserved does not mean archived.
Pipeline residue does not mean junk.
Workflow-discovery evidence does not mean ratified constitutional asset.

## 4. Current Runtime Classification Proposal
| thesis_id | Current Classification Proposal | Notes |
|---|---|---|
| 14 | Source-Context Record | Microsoft historical artifact / HRV-002 source context only. Not active HRV-002. |
| 7 | Archived Constitutional Asset | Kodak Roadmap-Archived / Type A Review Established. |
| 8 | Archived Constitutional Asset | NVIDIA NoTouch Validation / No-Touch Regression Reference. |
| 1 | Preserve — Substantive, Unsigned | NVIDIA Investment Thesis. Substantive but unsigned. Preserve pending authority. |
| 6 | Preserve — Substantive, Unsigned | Meta Platforms. Likely historical baseline candidate pending explicit sign-off. |
| 9 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Microsoft OVC-004. Preserve. Do not treat as junk. Not ratified archived asset. |
| 10 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Oracle OVC-004 PostFix. Preserve. Do not treat as junk. Not ratified archived asset. |
| 11 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Intel OVC-004 INT-001. Preserve. Do not elevate separately without external governance authority. |
| 12 | Evaluation-Pipeline Residue / Workflow-Discovery Evidence Pending Authority | Qualcomm OVC-004 INT-001. Preserve. Do not treat as junk. Not ratified archived asset. |
| 3 | Test / Junk / Manual Scratch Candidate | Manual-generated record candidate. No deletion authorized. |
| 4 | Test / Junk / Manual Scratch Candidate | Manual-generated record candidate. No deletion authorized. |
| 5 | Test / Junk / Manual Scratch Candidate | Manual-generated record candidate. No deletion authorized. |
| 13 | Test / Junk / Manual Scratch Candidate | Temporary FRICTION-003 validation record. No deletion authorized. |
| 2 | Orphan Reference / Referential Integrity Issue | Referenced in non-thesis tables but absent from theses. Repair not authorized. |

## 5. Records That Must Remain Untouched
At minimum, the following must remain untouched pending explicit authority:

- thesis_id=14
- thesis_id=7
- thesis_id=8
- thesis_id=1
- thesis_id=6
- thesis_id=9
- thesis_id=10
- thesis_id=11
- thesis_id=12
- thesis_id=2 orphan references

Untouched means:

- no deletion
- no overwrite
- no merge
- no migration
- no normalization
- no evidence relinking
- no lifecycle repair
- no active-work reclassification
- no archival ratification by implication

## 6. Cleanup Authority Classes
### Class A — Visibility Classification Only
Allowed future action:

- add an identity/classification metadata table or governed config
- classify runtime records without changing existing thesis/evidence/event rows

Not allowed:

- deletion
- row repair
- evidence relinking
- lifecycle repair
- Microsoft HRV-002 ratification

Recommended as first implementation class.

### Class B — Routing / UI Interpretation
Allowed future action:

- make Home, Portfolio, Workspace, Data Hygiene, and Data Explorer views read from classification authority

Not allowed:

- DB cleanup
- evidence changes
- deletion
- historical rewrite

### Class C — Orphan Reference Repair
Applies to:

- thesis_id=2 references in thesis_events and evidence_staging

Requirements before action:

- preservation plan
- before/after counts
- explicit repair authority
- rollback strategy or archival copy
- no silent deletion

Not authorized by this draft.

### Class D — Scratch/Test Record Disposition
Applies to:

- thesis_id=3
- thesis_id=4
- thesis_id=5
- thesis_id=13

Possible future dispositions:

- retain hidden
- archive as scratch/test
- quarantine from active views
- delete only with explicit deletion authority

Deletion is not authorized by this draft.

### Class E — Identity Ratification
Applies to:

- thesis_id=9
- thesis_id=10
- thesis_id=11
- thesis_id=12

thesis_id=1 and thesis_id=6 are not Class E identity-ratification records in this draft; their open question is sign-off, promotion, retirement, or continued preservation as substantive-but-unsigned records.

Rules:

- identity cannot be inferred from company name, ticker, or brand string
- thesis_id=11 remains grouped with 9/10/12 unless external governance authority proves otherwise
- preserved pending authority does not equal ratified archived status

### Class E2 — Substantive Unsigned Sign-Off
Applies to:

- thesis_id=1
- thesis_id=6

Purpose:

- determine whether substantive-but-unsigned records should be preserved as historical records, promoted through explicit governance sign-off, retired by explicit decision, or left unchanged pending later authority

Rules:

- sign-off cannot be inferred from data presence
- deletion is prohibited
- promotion requires explicit analyst approval
- retirement requires explicit analyst approval
- no evidence relinking or lifecycle repair is authorized by this class

### Class F — Evidence / Pillar Link Audit
Applies to:

- thesis_id=14
- thesis_id=1
- thesis_id=6
- thesis_id=7
- any record with pillar scores but no pillar_evidence_links

Purpose:

- determine whether existing pillar judgments are constitutionally supportable, assessment-only placeholders, or historical records requiring preservation but not reuse

Not allowed:

- automatic evidence relinking
- pillar score rewrite
- evidence migration
- score deletion
- retroactive governance repair

This class should produce a future audit artifact before any repair script exists.

### Class G — Evidence / Pillar Link Repair
Applies only after Class F audit.

Not authorized by this draft.

Requirements before future action:

- explicit evidence-link audit findings
- before/after link counts
- evidence provenance check
- analyst approval
- no automatic inference from related_pillar alone
- no retroactive rewriting of historical decision quality

## 7. Explicit Non-Authority
This draft does not authorize:

- DB mutation
- row deletion
- row repair
- row hiding
- evidence relinking
- evidence migration
- evidence ingestion
- Microsoft HRV-002 ratification
- HRV-002 successor creation
- Microsoft thesis_id=14 migration
- active-work routing changes
- cleanup commits
- classification metadata implementation
- Hermes startup
- SpaceX operational setup

## 8. Recommended Implementation Sequence
Phase 1 — Review and ratify or revise this cleanup authority draft.
Phase 2 — Add non-destructive runtime identity/classification metadata.
Phase 3 — Update UI routing to read from classification metadata.
Phase 4 — Scope ATHENA_PILLAR_EVIDENCE_LINK_AUDIT_DRAFT.md.
Phase 5 — Separately decide thesis_id=2 orphan reference repair.
Phase 6 — Decide sign-off disposition for thesis_id=1/6 and identity disposition for thesis_id=9/10/11/12.
Phase 7 — Decide scratch/test disposition for thesis_id=3/4/5/13.
Phase 8 — Revisit Microsoft Option A/B/C.
Phase 9 — Only then proceed to Hermes or SpaceX operational setup.

## 9. Initial Proposed Metadata Model
Proposed future table name:
athena_identity_authority

Suggested columns:

- id
- thesis_id
- identity_class
- governed_name
- validation_id
- authority_source
- authority_status
- active_work_allowed
- governance_attention_allowed
- archived_asset
- source_context_only
- workflow_discovery_residue
- cleanup_candidate
- deletion_allowed
- evidence_relink_allowed
- notes
- created_at
- updated_at

This is a proposed future metadata model only. No table creation or migration is authorized by this draft.

## 10. Pillar Evidence Link Compliance Gap
The hygiene report identifies a pillar-scores-without-links / assessment-only pillar pattern across substantive runtime records.

This is not merely data hygiene.
It is a constitutional compliance concern because Athena governed judgments must remain traceable to evidence.

This draft does not authorize repair.
The audit may propose whether pillar_evidence_links may be backfilled, whether scores must remain historical-only, or whether scores require re-evaluation. No relinking, score change, or evidence-link backfill is authorized by this document.

Recommended next artifact:
governance/design/ATHENA_PILLAR_EVIDENCE_LINK_AUDIT_DRAFT.md

Purpose of that future audit:

- identify which pillar judgments are evidence-linked
- identify which are assessment-only
- distinguish historical preserved judgments from reusable governed judgments
- define whether any evidence-link repair is permissible
- prevent retroactive rewriting of decision quality

## 11. Open Decisions
Required governance decisions:

- Should this cleanup authority draft be ratified?
- Should Athena add an identity authority metadata table?
- Should thesis_id=2 orphan references be preserved, repaired, quarantined, or left untouched?
- Should thesis_id=3/4/5/13 be hidden, archived as scratch/test, or retained only in Data Explorer?
- Should thesis_id=1 remain preserved as substantive-but-unsigned, be promoted through explicit sign-off, retired by explicit decision, or left unchanged pending later authority?
- Should thesis_id=6 remain preserved as substantive-but-unsigned, be promoted through explicit sign-off, retired by explicit decision, or left unchanged pending later authority?
- Should thesis_id=9/10/11/12 remain grouped as evaluation-pipeline residue pending authority?
- Is there external governance authority distinguishing thesis_id=11 from 9/10/12?
- Should a Pillar Evidence Link Audit be performed before any future evidence repair?
- Should Microsoft proceed under Option A, B, or C only after cleanup authority exists?

## 12. No-Mutation Guarantee
This draft creates no runtime authority by itself.
No DB mutation was performed.
No rows were inserted, updated, deleted, migrated, repaired, hidden, or relinked.
No active-work routing changed.
No HRV-002 action was taken.
No files were staged.
No commits were made.
