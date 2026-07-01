# VALIDATION_PORTFOLIO.md v1.0

## Document Metadata
Document: VALIDATION_PORTFOLIO.md

Version: 1.0

Effective Date: July 1, 2026

Status: Draft — Pending Review

Supersedes:

Previous Generation II validation roadmap references contained within the Athena Bootstrap and Phase I implementation planning.

Authority:

IMS Charter

Athena Bootstrap

Independent Audit Contract

GDR-001 — Validation Portfolio Rationalization

Hierarchy Placement:

This document is a governed validation artifact operating under the IMS Charter. It is parallel to, but distinct from, the design-authority chain defined in Athena Bootstrap Section 5. In the event of conflict, the IMS Charter controls. This document governs validation portfolio scope, validation status, archival classification, and Generation III validation entry requirements.

GDR-001 authorizes this version of the Validation Portfolio. VALIDATION_PORTFOLIO.md is the enduring governed artifact produced by that decision record.

## Purpose
The Validation Portfolio defines Athena's governed validation strategy.

Its purpose is to ensure Athena demonstrates constitutional compliance, operational readiness, reproducibility, and institutional learning through a focused set of governed validation programs.

This document is the authoritative source for Athena validation governance.

## Validation Philosophy
Athena validates constitutional capability.

Companies are selected because they exercise specific architectural capabilities.

Once those capabilities have been demonstrated or superseded, the company becomes an archived constitutional asset rather than an active roadmap dependency.

Athena validates systems, not companies.

Companies are evidence.

The architecture is the product.

## Canonical Validation Portfolio

### Active Validation Programs

## LVT-001 — SpaceX Operational Validation

### Purpose
Validate Athena as an operational analyst platform.

### Primary Objective
Demonstrate that Athena can support a governed analyst through the complete investment workflow while preserving constitutional integrity.

### Evidence Boundary
Snapshot S001 Evidence Cutoff:

May 20, 2026 S-1.

All Snapshot S001 reasoning must remain bounded to the governed evidence set available at the cutoff.

No score, recommendation, or conclusion for Snapshot S001 may rely on information outside the defined evidence boundary.

### Capabilities Validated

- Hermes monitoring
- Evidence acquisition
- Evidence grading
- Knowledge Record creation
- Assessment workflow
- Decision Gate
- Audit Trail
- Analyst-assisted operation
- Ready-for-Analyst workflow

### Success Criteria

- End-to-end governed workflow completed.
- Constitutional audit passes.
- Analyst actions fully traceable.
- Process reproducibility demonstrated, meaning the same governed evidence set produces materially consistent reasoning and recommendations independent of eventual investment outcome.

This validation does not require eventual investment success.

## HRV-002 — Microsoft Longitudinal Validation

### Purpose
Validate constitutional stability across time.

### Primary Objective
Demonstrate that Athena maintains reproducible reasoning and governance across a one-year historical investment cycle.

### Identifier Boundary
HRV-002 is the active Microsoft longitudinal validation cycle.

HRV-001 remains the historical closed Microsoft review cycle and must not be reused, relabeled, or overwritten.

### Capabilities Validated

- Historical replay
- Reproducibility
- Calibration stability
- Framework consistency
- Outcome Attribution
- Institutional learning

### Success Criteria

- Historical replay completed.
- Calibration remains constitutionally stable.
- Charter Outcome Attribution taxonomy exercised through a governed historical review.
- A resolved outcome classification, Type A, B, C1, C2, or D, is documented for the review period.
- If the resolved classification is Type A or Type C2, Kodak's designated Outcome Attribution regression role is fulfilled and may be retired following constitutional review.

HRV-002 may complete with a Type B, C1, or D classification. Such completion validates longitudinal review and taxonomy use, but it does not discharge Kodak's designated Outcome Attribution regression role.

## Archived Constitutional Assets
Archived assets preserve institutional knowledge and constitutional regression capability.

They are no longer active development priorities.

### Meta Platforms
Constitutional Purpose:

Historical regression baseline.

Ensures future architectural evolution does not introduce unintended behavioral regression.

### NVIDIA
Constitutional Purpose:

Fully automated no-touch pipeline regression.

Validates Athena's autonomous acquisition pipeline.

This remains constitutionally distinct from LVT-001 SpaceX, which validates the governed analyst-assisted operational workflow.

### Intel OVC
Constitutional Purpose:

Workflow-discovery regression.

Preserves the original Observe → OVC → INT operational validation sequence that informed Athena's analyst workflow architecture.

### Kodak
Constitutional Purpose:

Outcome Attribution regression reference.

Retirement Criterion:

Kodak remains the designated Outcome Attribution regression reference until HRV-002 produces a governed historical review containing a resolved Type A or Type C2 classification.

Upon successful constitutional review of that result, Kodak may be reclassified as a general archived regression asset.

If HRV-002 completes with a Type B, C1, or D classification, Kodak remains retained as the named Outcome Attribution regression reference.

If Generation III readiness is considered before a Type A or Type C2 case has been resolved, the unresolved Type A/C2 coverage gap must be explicitly documented as an accepted constitutional limitation in:

- VALIDATION_PORTFOLIO.md
- GDR-001 — Validation Portfolio Rationalization
- The Generation III readiness review

This dependency exists to ensure Outcome Attribution coverage remains visible and auditable until the Type A/C2 pathway is resolved or formally carried forward as an accepted Generation III limitation.

## Validation Governance
Validation exists to strengthen constitutional confidence.

Validation does not exist to maximize company coverage.

Additional validation companies require explicit constitutional justification tied to an uncovered architectural capability.

## Validation Record Schema

Each validation record shall maintain sufficient metadata to preserve reproducibility, auditability, falsifiability, and constitutional traceability.

Required fields:

| Field | Required |
|---|---|
| Validation ID | Yes |
| Validation Type | Yes |
| Company / Subject | Yes |
| Thesis ID | Yes, if applicable |
| Snapshot ID | Required for LVT records; N/A for HRV records |
| Evidence Cutoff | Yes |
| Evaluation Date | Yes |
| Review Date | Required for historical review |
| Decision Gate Status | Yes |
| Replay Sufficiency Score | Yes |
| Falsification Triggers Defined | Yes |
| Outcome Attribution Classification | Required once review is complete |
| Status | Yes |

Validation identifiers must not be reused across distinct governed reviews.

## Snapshot Constitutional Rules

Snapshot-based validation must preserve institutional history.

Rules:

1. Snapshot immutability.
2. Thesis inheritance.
3. Evidence date bounding.
4. Snapshot non-modification.
5. Decision Gate independence.
6. Snapshot Sequence Integrity.

Snapshot Sequence Integrity requires:

- snapshots are append-only;
- snapshots are created in chronological order;
- no ratified snapshot may later be inserted between existing snapshots;
- institutional history may not be rewritten through retroactive snapshot insertion.

LVT-001 Snapshot S001 is governed by these rules and is evidence-bounded to the May 20, 2026 S-1 cutoff.

## Replay Sufficiency

Replay Sufficiency is a governed field for both HRV and LVT validations.

| Score | Definition |
|---|---|
| Sufficient | Another analyst can reproduce the evaluation using only preserved evidence and governed records. |
| Partial | Core reasoning is reproducible, but important supporting evidence or rationale is incomplete. |
| Insufficient | The evaluation cannot be reproduced without external reconstruction or unstated assumptions. |
| Unknown | Formal Replay Sufficiency Assessment has not yet been performed. |

Replay Sufficiency supports reproducibility. It does not determine whether the investment outcome was successful.

## Superseded Portfolio Entries Table

The previous `VALIDATION_PORTFOLIO.md` contained a static Portfolio Entries table.

That table is superseded by the Canonical Validation Portfolio in this document.

The prior table also contained an identifier discrepancy: it listed `HRV-001` as Meta Platforms, while governed validation notes identify `HRV-001` as the closed Microsoft historical replay.

This document resolves the discrepancy by:

- preserving `HRV-001` as the historical closed Microsoft review cycle;
- assigning active Microsoft longitudinal validation to `HRV-002`;
- retaining Meta Platforms as an archived historical regression baseline rather than an HRV-001 record.

Do not restore the superseded table unless it is rebuilt from governed records and reviewed under the Validation Record Schema.

## PVP-001 Boundary

PVP-001 validates framework recurrence.

PVP-001 is not a portfolio management protocol.

PVP-001 does not authorize position sizing, cash management, trade execution, or portfolio operations.

Audit findings may serve as one evidence source for recurrence analysis, including Reasoning Recurrence Rate and Framework Analysis Finding eligibility, only under the frozen threshold:

- 1 case = Candidate Observation
- 2 cases = Candidate Pattern
- 3 or more cases = Framework Analysis Finding

Only findings with recurrence count of 3 or more are PVP-001 eligible.

## Generation III Entry Requirements
Generation III begins only after:

- Hermes operational.
- LVT-001 SpaceX Operational Validation complete.
- HRV-002 Microsoft Longitudinal Validation complete.
- Independent Audit Contract operational.
- THEMIS specification complete.
- Ready-for-Analyst workflow demonstrated.

Validation completion shall be evaluated against this document.

If HRV-002 completes without a Type A or Type C2 classification, Generation III may proceed only if Kodak remains retained as the named Outcome Attribution regression reference and the unresolved Type A/C2 coverage gap is explicitly documented as an accepted constitutional limitation.

## Relationship to Governance
This document is the governing authority for Athena validation strategy.

Referenced by:

- IMS Charter
- Athena Bootstrap
- Independent Audit Contract
- GDR-001 — Validation Portfolio Rationalization
- THEMIS Specification

## Guiding Principle
Athena validates constitutional capability.

Companies are evidence.

The architecture is the product.
