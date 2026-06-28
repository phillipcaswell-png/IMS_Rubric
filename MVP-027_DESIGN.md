Document Authority: Versioned
Governed By: IMS Charter v1.0
Document Owner: Athena Architecture
Current Version: 1.0
Effective Date: June 2026
Purpose: Define the Athena Evidence Synthesis capability for Business Quality orchestration.
Scope: Read-only synthesis of governed observations and advisory extraction signals for analyst pre-briefing. Excludes scoring, judgment generation, persistence, schema changes, and workflow redesign.
Implements Charter Principles: 1, 3, 5
May Modify: Athena evidence orchestration implementation for MVP-027.
May Not Modify: Constitutional responsibilities defined by the IMS Charter, ATHENA_ARCHITECTURE.md, or THEIA_SPECIFICATION.md.
Dependencies:
- IMS Charter v1.0
- ATHENA_ARCHITECTURE.md
- THEIA_SPECIFICATION.md
Supersedes: None
Superseded By:

# MVP-027 — Athena Evidence Synthesis

## 1. Purpose

### Objective

Introduce Athena Evidence Synthesis, a read-only orchestration capability that assembles pillar-specific evidence immediately prior to analyst scoring.

Athena shall organize governed observations and advisory extraction signals into a single synthesis while preserving the constitutional separation of orchestration, observation, judgment, and governance.

This document is governed by the IMS Charter v1.0.

Athena orchestration responsibilities are defined in ATHENA_ARCHITECTURE.md.

Theia advisory responsibilities are defined in THEIA_SPECIFICATION.md.

---

## 2. Background

MVP-023 established Theia's Extraction Capability.

Individual evidence items can now produce advisory extraction signals, but analysts must manually aggregate observations across multiple filings before evaluating a Business Quality pillar.

Evidence synthesis remains a manual activity.

MVP-027 transfers this orchestration responsibility to Athena without changing analyst authority or constitutional boundaries.

---

## 3. Scope

### Included

- New orchestration service: get_athena_evidence_synthesis(thesis_id, pillar_id)
- Read-only evidence synthesis
- Business Quality UI integration
- Coverage metrics
- Traceability to originating evidence

### Excluded

- Scoring
- Judgment generation
- Observation creation
- Evidence editing
- Dashboard redesign
- Schema changes
- Database migrations
- Persistence of synthesis output

---

## 4. Service Contract

### Service

get_athena_evidence_synthesis(
    thesis_id: int,
    pillar_id: str
)

Returns:

{
    "pillar_id": str,
    "pillar_label": str,
    "governed_observations": [...],
    "advisory_signals": [...],
    "supporting_evidence": [...],
    "coverage": {
        "governed_observation_count": int,
        "advisory_signal_count": int,
        "evidence_item_count": int
    }
}

The response contract is frozen for MVP-027.

---

## 5. Architecture

### Service Boundary

All orchestration shall reside within services.py under Athena orchestration services.

The UI:
- shall not query evidence_observations
- shall not query evidence_items
- shall not invoke extraction services
- shall render only the returned synthesis model

No orchestration logic shall exist in streamlit_app.py.

---

## 6. Data Sources

Primary source:
- evidence_observations

Secondary source (advisory only):
- get_extraction_suggestions()

Supporting metadata:
- evidence_items

Extraction suggestions shall be used only when governed observations are sparse or absent and only after analyst-initiated extraction has already occurred.

MVP-027 shall never initiate extraction.

---

## 7. User Experience

Location:
Business Quality tab

Placement:
Immediately above the Business Quality scoring form.

Behavior:
The synthesis refreshes automatically whenever the selected pillar changes.

Display order is fixed:
1. Governed Observations
2. Advisory Extraction Signals
3. Supporting Evidence
4. Coverage Summary

Governed observations shall always appear before advisory content.

Every advisory item shall be labeled:
Advisory Extraction Signal

Every governed item shall be labeled:
Governed Observation

---

## 8. Operational Constraints

The synthesis path is strictly read-only.

Implementation shall not:
- create observations
- invoke extraction generation
- log events
- write audit records
- mutate database state
- perform INSERT
- perform UPDATE
- perform DELETE

Only transient UI display state may change.

Deterministic ordering shall be preserved:

Supporting Evidence:
  publication_date ASC, evidence_item_id ASC

Governed Observations:
  publication_date ASC, observation_id ASC

Advisory Signals:
  publication_date ASC, source_location ASC

---

## 9. Validation

Implementation succeeds when:

1. Synthesis appears above Business Quality scoring.
2. Pillar changes refresh synthesis.
3. Governed observations appear first.
4. Advisory items remain clearly identified.
5. Traceability exists for every displayed item.
6. Coverage counts are accurate.
7. Read-only behavior is preserved.
8. Observation counts remain unchanged.
9. Existing Business Quality workflow is unchanged.
10. Existing Athena Dashboard behavior is unchanged.

Regression testing shall additionally verify:
- extraction workflow unchanged
- observation workflow unchanged
- evidence editing unchanged
- score persistence unchanged

---

## 10. Completion Criteria

MVP-027 is complete when Athena provides a reusable orchestration service that assembles pillar-specific evidence while preserving constitutional responsibilities and introducing no new persistence, schema changes, workflow regressions, or architectural boundary violations.

The service becomes the canonical evidence synthesis interface for future Athena capabilities.
