<!-- Status: Historical Design Record -->

# MVP-024 Design Container
Implements: THEIA_SPECIFICATION.md

Constitutional boundaries: See THEIA_SPECIFICATION.md — not restated here.

---

## Purpose
Introduce Theia Core Ingestion by allowing Athena to discover and stage authoritative SEC EDGAR filings for analyst review.

This MVP establishes automated evidence discovery while preserving analyst control over every governed lifecycle transition.

---

## Scope
MVP-024 adds only:

- SEC EDGAR evidence discovery
- Evidence staging
- Metadata normalization
- Authoritative publication-date capture
- Deduplication
- Amendment detection

This MVP does not include:

- Evidence promotion
- Observation creation
- Scoring
- Recommendations
- Pipeline orchestration
- Workspace redesign
- Non-EDGAR evidence sources

---

## Theia Component
Core

Core capability implemented:

- Ingestion

Current maturity:

Level 0 (Planned)

Target after successful implementation and validation:

Level 1 (Experimental)

---

## Evidence Sources
Permitted source:

- SEC EDGAR only

Publication dates:

- Must originate from authoritative EDGAR metadata
- Must never be inferred from document content

---

## Evidence Lifecycle
Theia may:

External Source
-> Discovery
-> Metadata Normalization
-> Deduplication
-> Pending evidence_staging

Theia must never:

Pending
-> Reviewed
-> Confirmed
-> Promoted

Those transitions remain analyst-controlled.

---

## Deduplication Policy
Primary key:

- SEC accession number

Secondary key:

- Source URL

Amendments:

- 10-K/A
- 10-Q/A

Requirements:

- Stage separately
- Explicitly identify as amendments
- Never replace the original filing
- Analyst decides which version, if any, is promoted

---

## Design Constraints
Retain existing constraints:

- SEC EDGAR only
- EDGAR metadata dates only
- Never infer publication dates
- Never promote evidence
- Analyst controls lifecycle
- Accession number primary
- Source URL secondary

---

## Service Expectations
New advisory/core service:

- ingest_sec_filings(...)

Characteristics:

- Creates staging records only
- Never writes governed evidence
- Never performs promotion
- Returns staged identifiers for analyst review

No implementation details.

No API endpoint specifications.

No HTTP library choices.

---

## UI Expectations
Minimal additions only:

- Discover Evidence action
- Staging summary
- Amendment indicator
- Duplicate warning

No workspace redesign.

---

## Non-Goals

- No promotion automation
- No observations
- No scoring
- No recommendations
- No pipeline orchestration
- No non-EDGAR sources
- No document extraction

---

## Verification Requirements
Implementation is complete only when all are true:

- SEC filings successfully staged
- Publication dates originate from EDGAR metadata
- Duplicate filings prevented through accession-number matching
- Source URL secondary deduplication functions correctly
- Amendments staged separately
- Amendments clearly flagged
- No automatic promotion occurs
- Analyst controls every lifecycle transition
- Existing MVP-022 workflow unchanged
- Validation Case 002 successfully stages Kodak filings

---

## MVP-Specific Risks
Include only risks unique to MVP-024:

- EDGAR rate limiting
- SEC terms-of-service compliance
- Metadata quality variations
- Amendment handling confusion
- Duplicate accession-number edge cases

---

## Policy Requirements
State policy only:

- Respect SEC rate limits
- Respect SEC terms of service
- Use authoritative metadata only

Do not specify implementation.

---

## Do-Not-Build Warnings
Do not:

- Infer publication dates
- Promote evidence
- Score evidence
- Create observations
- Recommend investments
- Add non-EDGAR sources
- Expand into MVP-025 pipeline orchestration
- Expand into MVP-026 workspace functionality
