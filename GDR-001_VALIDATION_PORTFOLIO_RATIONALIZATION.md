# GDR-001 — Validation Portfolio Rationalization

## Document Metadata
Document: GDR-001_VALIDATION_PORTFOLIO_RATIONALIZATION.md

Decision Type: Governance Decision Record

Effective Date: July 1, 2026

Status: Draft — Pending Review

Governing Authority:

IMS Charter

Athena Bootstrap

Authorized Artifact:

VALIDATION_PORTFOLIO.md v1.0

## Decision Summary
Athena's validation strategy is rationalized from a Phase I company-project roadmap into a Canonical Validation Portfolio.

The active validation program is reduced to two standing validation streams:

1. LVT-001 — SpaceX Operational Validation
2. HRV-002 — Microsoft Longitudinal Validation

Prior company-specific validation projects are retained as archived constitutional assets with named regression purposes.

This decision simplifies the active governance surface while preserving institutional learning and constitutional regression coverage.

## Decision Classification
This is a Governance Decision Record, not an Experience Before Architecture change.

The decision is not based on a new operational finding from Hermes, SpaceX, or Microsoft.

It is based on architectural maturation and deliberate governance scope simplification.

This decision supersedes the earlier informal GSS-001 classification. The final classification is GDR-001.

## Rationale
Athena has matured beyond a collection of company-specific validation projects.

Earlier validation cases were necessary to test constitutional mechanisms, analyst workflow, historical replay, automation, and outcome attribution.

Those projects are no longer the active roadmap.

Athena now validates constitutional capability through standing validation programs.

Companies serve as evidence and regression references.

The architecture is the product.

## Identifier Decision
This GDR preserves governed validation identifiers.

LVT-001 identifies SpaceX Operational Validation.

Snapshot S001 identifies the first SpaceX snapshot.

Snapshot S001 is evidence-bounded by the May 20, 2026 S-1 cutoff.

HRV-002 identifies the active Microsoft Longitudinal Validation cycle.

HRV-001 remains a historical closed review and must not be reused, relabeled, or overwritten.

Reusing HRV-001 for the new Microsoft cycle would create an auditability conflict by assigning one governed identifier to two distinct validation records.

## Prior Portfolio Identifier Discrepancy

The previous `VALIDATION_PORTFOLIO.md` contained a static Portfolio Entries table that listed `HRV-001` as Meta Platforms.

Other governed repository records identify `HRV-001` as the closed Microsoft historical replay.

This GDR resolves the discrepancy by:

- preserving `HRV-001` as the historical closed Microsoft review cycle;
- assigning active Microsoft longitudinal validation to `HRV-002`;
- retaining Meta Platforms as an archived historical regression baseline;
- prohibiting reuse of `HRV-001` for new active validation work.

The superseded table shall not be restored unless rebuilt from governed records and reviewed under the Validation Record Schema.

## Active Validation Scope

### LVT-001 — SpaceX Operational Validation
LVT-001 validates whether Athena can operate as a governed analyst-assisted daily workspace.

Snapshot S001 Evidence Cutoff:

May 20, 2026 S-1.

It exercises:

- Hermes monitoring
- Evidence acquisition
- Evidence grading
- Knowledge Record creation
- Assessment workflow
- Decision Gate
- Audit Trail
- Ready-for-Analyst workflow
- Analyst-in-the-loop governance

LVT-001 validates process reproducibility, not eventual investment outcome.

### HRV-002 — Microsoft Longitudinal Validation
HRV-002 validates whether Athena remains constitutionally consistent over a one-year historical investment cycle.

It exercises:

- Historical replay
- Reproducibility
- Calibration stability
- Outcome Attribution
- Framework consistency
- Institutional learning

HRV-002 must produce a governed historical review with a resolved Type A, B, C1, C2, or D classification.

HRV-002 may complete with any valid resolved classification.

However, only a Type A or Type C2 classification discharges Kodak's designated Outcome Attribution regression role.

## Archived Validation Scope
The following projects are removed from the active roadmap and retained as archived constitutional assets.

### Meta Platforms
Archived Constitutional Purpose:

Historical regression baseline.

### NVIDIA
Archived Constitutional Purpose:

Fully automated no-touch pipeline regression.

NVIDIA remains distinct from LVT-001 SpaceX. NVIDIA represents the fully automated pipeline reference. LVT-001 SpaceX represents the analyst-assisted operational workflow.

### Intel OVC
Archived Constitutional Purpose:

Workflow-discovery regression.

Intel OVC preserves the Observe → OVC → INT discovery path that informed Athena's operational workflow.

### Kodak
Archived Constitutional Purpose:

Outcome Attribution regression reference.

Kodak remains the designated Outcome Attribution regression reference until HRV-002 produces a governed historical review containing a resolved Type A or Type C2 classification.

HRV-002 may complete with a Type B, C1, or D classification. That validates longitudinal review and taxonomy use, but it does not discharge Kodak's Outcome Attribution regression role.

Kodak may be reclassified as a general archived regression asset only after:

1. HRV-002 produces a resolved Type A or Type C2 classification.
2. The result passes constitutional review.
3. VALIDATION_PORTFOLIO.md is updated to record the retirement.

If HRV-002 completes without a Type A or Type C2 classification, Kodak remains retained as the named Outcome Attribution regression reference.

## Kodak / Generation III Rule
An unresolved Type A/C2 Outcome Attribution gap does not automatically block Generation III entry.

Generation III may proceed if HRV-002 completes with a Type B, C1, or D classification, provided that:

1. Kodak remains retained as the named Outcome Attribution regression reference.
2. The unresolved Type A/C2 coverage gap is explicitly documented in VALIDATION_PORTFOLIO.md.
3. The unresolved Type A/C2 coverage gap is explicitly documented in this GDR.
4. The unresolved Type A/C2 coverage gap is explicitly documented in the Generation III readiness review.

This rule preserves auditability without treating every unresolved validation pathway as an automatic blocker.

The Type A/C2 gap remains a declared constitutional limitation until resolved through HRV-002 or a future governed validation case.

## Generation III Readiness Review Authority
This GDR does not create a new independent decision-making body.

The Generation III readiness review is a governed review event conducted under the existing IMS Charter, Athena Bootstrap, VALIDATION_PORTFOLIO.md, Independent Audit Contract, and applicable governance records.

Its purpose is to determine whether documented entry criteria have been satisfied or whether any unresolved constitutional limitation is explicitly accepted and carried forward.

The readiness review may not override the IMS Charter.

The readiness review may not silently waive validation gaps.

Any accepted limitation must be documented in the readiness review output and carried forward into the next applicable governance artifact.

## Impact Statement
The active evidentiary base narrows from multiple Phase I company profiles to two active validation streams.

This narrowing is deliberate.

It reduces roadmap complexity while preserving archived regression coverage.

Outcome Attribution Type A/C2 taxonomy coverage currently rests on a pending active case, not a resolved active precedent.

Kodak is retained as the named regression reference until HRV-002 produces a governed Type A or Type C2 classification or until the unresolved Type A/C2 gap is explicitly accepted and carried forward during Generation III readiness review.

No constitutional principles are changed.

No decision methodology is changed.

No implementation behavior is changed.

The active governance surface is simplified while preserving archived constitutional evidence.

## Generation III Implications
Generation III entry now depends on six conditions:

1. Hermes operational.
2. LVT-001 SpaceX Operational Validation complete.
3. HRV-002 Microsoft Longitudinal Validation complete.
4. Independent Audit Contract operational.
5. THEMIS specification complete.
6. Ready-for-Analyst workflow demonstrated.

Completion of HRV-002 does not automatically retire Kodak unless the Type A or Type C2 condition is satisfied.

Generation III may proceed if HRV-002 completes with a Type B, C1, or D classification, provided Kodak remains retained as the Outcome Attribution regression reference and the unresolved Type A/C2 coverage gap is explicitly documented as an accepted constitutional limitation.

## Governance Controls
Future validation companies may be added only when they exercise a constitutionally distinct capability not already covered by the active or archived portfolio.

Archived assets may be reactivated only for:

- Regression testing
- Constitutional review
- Audit validation
- Framework-change validation
- Uncovered capability testing

Reactivation must be documented in VALIDATION_PORTFOLIO.md.

## Decision Outcome
Draft — Pending Review.

Proposed active validation roadmap:

- LVT-001 — SpaceX Operational Validation
- HRV-002 — Microsoft Longitudinal Validation

Proposed archival classification:

- Meta Platforms — historical regression baseline
- NVIDIA — fully automated no-touch pipeline regression
- Intel OVC — workflow-discovery regression
- Kodak — Outcome Attribution regression reference

All prior Phase I company-specific validation projects are proposed for archival classification as constitutional assets with named regression purposes.
