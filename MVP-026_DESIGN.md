<!-- Status: Historical Design Record -->

# MVP-026 Design Container
Implements: THEIA_SPECIFICATION.md

Constitutional boundaries: See THEIA_SPECIFICATION.md — not restated here.

---

## Purpose
MVP-026 introduces Theia Core Workspace Enhancement by improving the existing Evidence tab into a unified analyst workspace.

This MVP enhances the existing workflow without replacing the Evidence tab architecture, altering service-layer authority, or modifying governed lifecycle behavior.

The objective is to improve analyst efficiency while preserving every constitutional boundary established by MVP-022 through MVP-025.

---

## Scope
MVP-026 adds only:

- Incremental enhancement of the existing Evidence tab
- Document viewer
- Ephemeral suggestion panel
- Integration surface for MVP-023 Extraction Capability
- Observation visibility panel
- Evidence lifecycle visibility
- Unified analyst workflow

This MVP does not include:

- Application-wide redesign
- Replacement of the Evidence tab
- Evidence ingestion
- Pipeline orchestration
- Automatic observation creation
- Promotion automation
- Scoring
- Recommendations

---

## Theia Component
Core

Core capability implemented:

- Workspace

Current maturity:

Level 0 (Planned)

Target after successful implementation and validation:

Level 1 (Experimental)

---

## Workspace Responsibilities
The workspace may surface:

- Evidence lifecycle state
- Selected promoted evidence
- Existing governed observations
- Ephemeral extraction suggestions
- Advisory pillar signals
- Advisory confidence indicators
- Blank Observation Form entry point

The workspace must never:

- Create observations automatically
- Pre-populate observation_text
- Store suggestion output
- Log suggestion output
- Promote evidence automatically
- Score evidence
- Score business pillars
- Recommend investments

---

## Relationship to MVP-023
The suggestion panel references MVP-023 Extraction Capability.

Suggestions remain:

- Ephemeral
- Advisory
- Non-governed
- Not stored
- Not logged

The workspace provides presentation only.

It does not alter the constitutional behavior of the Extraction Capability.

---

## Governed Workflow Preservation
The existing governed sequence remains unchanged:

Stage
-> Review
-> Confirm
-> Promote
-> Observe

The existing MVP-022 governed observation workflow remains authoritative.

Existing service-layer writes remain authoritative.

Existing audit trail behavior remains authoritative.

---

## Design Constraints

- Incremental enhancement only
- Existing Evidence tab preserved
- No tab architecture replacement
- No application-wide redesign
- Suggestion output never stored
- Suggestion output never logged
- Observation form remains analyst-authored
- Existing service-layer writes preserved
- Existing audit trail preserved
- Existing governed workflow preserved

---

## Service Expectations
No new governed write authority.

Workspace may call existing services to surface:

- Evidence items
- Evidence staging records
- Evidence observations
- Extraction suggestions

No implementation details.

No algorithms.

No framework-specific implementation.

---

## UI Expectations
Minimal additions only:

- Document viewer
- Suggestion panel
- Observation visibility panel
- Open Observation Form entry point
- Evidence lifecycle context

No application redesign.

No replacement of the existing Evidence tab.

---

## Non-Goals

- No application architecture redesign
- No Evidence tab replacement
- No promotion automation
- No scoring
- No recommendations
- No automatic observations
- No evidence ingestion
- No pipeline orchestration

---

## Verification Requirements
Implementation is complete only when all are true:

- Existing Evidence tab continues functioning
- Document viewer displays selected promoted evidence
- Suggestion panel references MVP-023 Extraction Capability
- Suggestions remain ephemeral
- Suggestion output is never stored
- Suggestion output is never logged
- Observation workflow uses existing MVP-022 governed path
- Existing service-layer writes remain unchanged
- Existing audit trail remains unchanged
- Stage -> Review -> Confirm -> Promote -> Observe sequence preserved
- Validation Case 002 executes successfully

---

## MVP-Specific Risks
Include only risks unique to workspace enhancement:

- UI confusion between advisory suggestions and governed observations
- Workspace scope creep
- Analyst misunderstanding visible suggestions as governed evidence
- Future pressure to merge suggestion panel with the observation form

---

## Policy Requirements
State policy only:

- Workspace improves analyst visibility.
- Workspace does not expand Theia constitutional authority.
- Workspace does not alter governed lifecycle transitions.
- Workspace completion must never imply evidence approval, analyst review completion, or investment decision readiness.

Do not specify implementation.

---

## Do-Not-Build Warnings
Do not:

- Replace the Evidence tab
- Redesign the application
- Store suggestions
- Log suggestion output
- Pre-populate observation_text
- Create observations automatically
- Promote evidence
- Score evidence
- Expand into MVP-023 implementation
- Expand into MVP-024 ingestion
- Expand into MVP-025 pipeline orchestration
- Introduce implementation details
