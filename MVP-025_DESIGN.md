<!-- Status: Historical Design Record -->

# MVP-025 Design Container
Implements: THEIA_SPECIFICATION.md

Constitutional boundaries: See THEIA_SPECIFICATION.md — not restated here.

---

## Purpose
MVP-025 introduces Theia Core Pipeline Orchestration, coordinating evidence discovery through staging while preserving all constitutional boundaries.

This MVP automates orchestration only and does not automate analyst judgment.

---

## Scope
Include only:

- Discovery orchestration
- Evidence staging orchestration
- Pipeline status tracking
- Hermes workflow notification
- EDGAR-only operation (until MVP-024 proven)

Explicitly exclude:

- Promotion
- Scoring
- Observation creation
- Workspace redesign
- Non-EDGAR sources

---

## Theia Component
Core

Core capability implemented:

- Pipeline Orchestration

Current maturity:

Level 0 (Planned)

Target after implementation:

Level 1 (Experimental)

---

## Pipeline Responsibilities
Theia may coordinate:

Discovery
-> Deduplication
-> Metadata normalization
-> evidence_staging

Theia must never coordinate:

Reviewed
-> Confirmed
-> Promoted
-> Observed

Those remain analyst-controlled.

---

## Hermes Integration
Policy only.

Hermes receives a workflow event indicating staging completion.

Do not describe implementation.

Do not describe messaging technology.

Do not describe event transport.

---

## Pipeline Status Panel
Information surfaced:

- Documents discovered
- Documents staged
- Duplicate count
- Amendment count
- Awaiting analyst review

Do not describe UI implementation.

---

## Design Constraints
Include:

- EDGAR-only until MVP-024 validated
- No automatic promotion
- No automatic scoring
- No automatic observations
- Analyst controls every governed transition
- Existing evidence lifecycle unchanged

---

## Service Expectations
New orchestration service:

run_evidence_pipeline(...)

Characteristics:

- Coordinates existing services
- Creates staging records only
- Never promotes
- Never creates observations
- Returns pipeline summary

No implementation details.

No algorithms.

No HTTP details.

---

## UI Expectations
Minimal additions only:

- Discover Evidence action
- Pipeline Status panel
- Hermes completion notification

No workspace redesign.

---

## Non-Goals
Explicitly include:

- No promotion automation
- No scoring
- No recommendations
- No observations
- No workspace redesign
- No non-EDGAR evidence
- No document extraction

---

## Verification Requirements
Implementation complete only when:

- Discovery populates staging
- Duplicate handling verified
- Pipeline summary accurate
- Hermes completion workflow generated
- No automatic promotion
- No automatic scoring
- No automatic observations
- Existing MVP-022 workflow unchanged
- Existing MVP-024 ingestion unchanged
- Validation Case 002 executes successfully

---

## MVP-Specific Risks
Include only risks unique to orchestration:

- Pipeline interruption
- Partial discovery completion
- Duplicate workflow notifications
- Analyst misunderstanding pipeline completion as evidence approval

---

## Policy Requirements
State only:

- Pipeline coordinates services
- Pipeline never expands constitutional authority
- Pipeline failures never bypass analyst review
- Pipeline status reflects orchestration state only.
- Pipeline completion must never imply evidence quality, analyst review, or constitutional approval.

No implementation.

---

## Do-Not-Build Warnings
Do not:

- Promote evidence
- Score evidence
- Create observations
- Introduce non-EDGAR sources
- Redesign workspace
- Expand into MVP-026
- Introduce implementation details
