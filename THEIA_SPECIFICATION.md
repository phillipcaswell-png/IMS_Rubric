# THEIA Specification

## Constitutional Position
Evidence perception and discovery agent.

## Constitutional Authority
Constitutional authority:
- IMS Charter v1.0
- GOVERNANCE_NOTES.md

Engineering authority:
- ATHENA_ARCHITECTURE.md
- AGENT_SPECIFICATION_STANDARD.md

Specification authority:
- THEIA_SPECIFICATION.md

Theia derives its authority from these governing documents.
Theia derives no authority from its implementation.

## Mission
Makes the external world visible to Athena's governed evaluation process. Theia may observe. Only Themis may judge.

## Responsibilities
- Discover evidence candidates from approved sources
- Stage evidence candidates for governed intake review
- Surface authoritative source metadata to analysts
- Coordinate intake readiness for governed lifecycle transitions
- Observe external filings and document updates for analyst review

## Explicit Prohibitions
- Must never score
- Must never recommend
- Must never promote
- Must never write governed records
- Must never override analyst judgment
- Must never bypass constitutional gates
- Must never write to evidence_observations

## Non-Goals
- Entity Recognition capability implementation in this version
- Timeline Extraction capability implementation in this version
- Financial Statement Parsing capability implementation in this version
- Risk Detection capability implementation in this version
- Any autonomous decision or recommendation functionality
- Any automatic scoring, promotion, or governed observation authoring

## Trust Model
Advisory.

## Read Permissions

- evidence_items
- evidence_staging
- evidence_observations

## Write Permissions

- evidence_staging (staging transitions only)

## Prohibited Writes

- evidence_items
- evidence_observations
- decision_logs
- thesis_reviews

## Inputs and Surfaces
- Inputs: external filings/documents and source metadata
- Surfaces: staged evidence candidates, metadata, and analyst-facing advisory signals

## Governance Constraints
- Publication Date Policy: authoritative metadata only, never inferred from document content
- Deduplication Policy: accession number primary, source URL secondary, amendments flagged separately
- Never promotes evidence
- Analyst controls all lifecycle transitions

## Failure Philosophy

If Theia is unavailable:

- Evidence discovery may pause.
- Governed workflows continue.
- Analysts may perform evidence collection manually.
- Constitutional gates remain enforceable.
- The system must fail safely rather than silently.

## Audit Expectations
Log invocation events only, never log suggestion output, advisory output must never become a shadow governed record.

## Theia Capability Model
### Core
- Registry
- Ingestion
- Metadata
- Deduplication
- Lifecycle

### Capabilities (presented as Skills in UI)
- Extraction
- Passage Detection
- Entity Recognition
- Timeline Extraction
- Financial Statement Parsing
- Risk Detection

## Capability Registry
| Capability | Purpose | Inputs | Surfaces | UI Name | Status | Maturity | MVP |
|---|---|---|---|---|---|---|---|
| Extraction | Surface potentially relevant passages from promoted evidence for analyst review | Promoted evidence document text | Ephemeral suggested passages | Extraction Skill | Implemented | Level 1 — Experimental | MVP-023 |
| Passage Detection | Identify document passages that may relate to governed pillars | Promoted evidence document text | Advisory passage candidates and pillar signals | Passage Detection Skill | Implemented | Level 1 — Experimental | MVP-023 |
| Entity Recognition | Identify companies, people, products, geographies, and organizations in evidence | Evidence document text | Advisory entity list | Entity Recognition Skill | Future | Level 0 | TBD |
| Timeline Extraction | Identify dated events and sequence them for analyst review | Evidence document text and metadata | Advisory timeline candidates | Timeline Extraction Skill | Future | Level 0 | TBD |
| Financial Statement Parsing | Extract structured financial statement items for analyst review | Filings and financial tables | Advisory financial data candidates | Financial Statement Parsing Skill | Future | Level 0 | TBD |
| Risk Detection | Surface risk disclosures and risk-related changes across evidence | Filings and disclosures | Advisory risk candidates | Risk Detection Skill | Future | Level 0 | TBD |

## Validation Requirements
Capabilities advance only through historical validation reviewed by analysts.

## Implemented By
- MVP-023
- MVP-024
- MVP-025
- MVP-026

## Change Control
The following changes require constitutional review before implementation:

- Mission
- Responsibilities
- Explicit Prohibitions
- Trust Model
- Read/Write Permissions
- Capability Model
- Capability Maturity Level 3 promotion

Implementation details may evolve provided they do not alter Theia's constitutional behavior.
