Athena Development Standard (v1.3.0)

Purpose:
Define the required development and release discipline for Athena capabilities while preserving constitutional boundaries.

Athena Development Cycle:
1. Define problem
2. Freeze constitutional boundaries
3. Freeze architectural boundaries
4. Define measurable success criteria
5. Implement smallest viable capability
6. Validate regression
7. Use on real work
8. Record operational friction
9. Design next MVP

MVP Definition Standard:
- Every MVP must state one objective in plain language.
- Every MVP must define explicit non-objectives.
- Every MVP must define measurable success criteria before implementation.
- Every MVP must name constitutional boundaries that cannot change.
- Every MVP must name architectural boundaries that cannot change.
- Every MVP must identify owner subsystem(s) for each new output field.
- Every MVP must include a verification procedure before approval.

Regression Policy:
- Validation Case 001 remains mandatory for milestone regression safety.
- Regression checks must verify constitutional gates are unchanged unless explicitly governed.
- Regression output must be recorded in repository documentation.
- If regression fails, release progression is blocked until resolved.

Release Policy:
- Release tags must correspond to validated milestone states.
- Documentation updates required by the milestone must be completed before release tag publication.
- No release may include undocumented constitutional behavior changes.
- Release notes must state objective, non-objectives, and verification outcome.

Review Expectations:
- Reviews prioritize constitutional safety over feature completeness.
- Reviewers must verify no unauthorized authority expansion occurred.
- Reviewers must verify ownership provenance for orchestrated outputs.
- Reviewers must verify no governed writes occur in read-only orchestration features.
- Reviewers must confirm residual risks and deferred intentions are documented.

## Validation Case Standard

Every historical validation case requires a Validation Freeze Record before the first evidence item is staged.

The freeze record is immutable after staging begins.

Required freeze record contents:
- Evaluation date
- Evidence cutoff date
- Validation mode confirmation
- Primary review horizon
- Validation question
- Validation hypothesis
- Evidence sequencing protocol
- Explicit statement: no expected decision, scores, or outcome recorded
- Explicit statement: no expected attribution recorded

Case-specific execution details (workflow friction, outcome attribution, lessons) are recorded in VALIDATION_NOTES.md under the individual case.

The methodology standard lives here. The execution record lives in VALIDATION_NOTES.md.

---

## Three Governance Domains

Athena has three distinct governance domains. Each domain has
a primary governing document. The Development Standard does not
duplicate content owned by other documents — it references them.

| Domain | Primary Document | Question it answers |
|--------|-----------------|---------------------|
| Constitutional Governance | IMS Charter | What is Athena allowed to do? |
| Engineering Governance | ATHENA_DEVELOPMENT_STANDARD.md | How do we change Athena? |
| Experience Governance | ATHENA_UX_PRINCIPLES.md, ATHENA_DESIGN_SYSTEM.md, ATHENA_INTERFACE_MOCKUP.md, ATHENA_COMPONENT_LIBRARY.md | How should Athena present itself? |

For the four-layer architectural model, see ATHENA_ARCHITECTURE.md.
This document references that model but does not duplicate it.

---

## Change Control Matrix

| Change Type | Level | Required Review | Required Updates |
|-------------|-------|-----------------|------------------|
| Visual styling | L1 | Design | Design System if applicable |
| New UI component | L1 | Design | Component Library |
| Navigation or workflow | L2 | Design + Architecture | Interface Mockup, Component Library, Implementation Plan |
| New service | L3 | Architecture | Architecture, Development Standard |
| Agent capability expansion | L3 | Architecture + Capability Review | Agent Specification, Capability Specification |
| Constitutional rule | L3 | Constitutional Review | IMS Charter, Architecture, Development Standard |

---

## Post-v2.0 Governance Levels

Every proposed change after v2.0 must be classified before
implementation begins.

| Level | Scope | Approval Required |
|-------|-------|-------------------|
| L1 — Presentation | Colors, typography, layout, components, UX polish | Design review only |
| L2 — Workflow | Navigation, analyst flow, sequencing, interaction | Design + architecture review |
| L3 — Constitutional | Agent responsibilities, governance rules, scoring model, decision authority, persistence, audit behavior | Formal architecture review + historical validation |

A change that appears to be L1 but touches L3 behavior must be
reclassified before implementation proceeds. Classification is
determined by what changes, not by how the change is described.

---

## Principle of Proportional Governance

The level of review should be proportional to the potential
impact of the change.

Changes that materially affect analyst decisions, historical
reproducibility, constitutional authority, or governance
boundaries require the highest level of review.

Editorial, explanatory, or clarifying updates that do not alter
behavior should follow the appropriate review process but do not
require re-validation.

---

## Architecture Preservation Rule

New capabilities should be added within the existing architectural
layers whenever reasonably possible.

A proposal that requires modifying multiple architectural layers
should first demonstrate why the capability cannot be achieved by
extending existing responsibilities.

Extending a layer is preferred over redefining it.

---

## v2.0 Beta Exit Criteria

v2.0 is reached when all of the following are true.

Functional:
- Complete a thesis from evidence staging through Mnemosyne
  review without database intervention
- No manual SQL required during normal analyst workflow
- All constitutional gates enforce correctly

UX:
- Every mode matches the approved interface mockup
- Every reusable component comes from the component library
- No legacy Streamlit layouts remain in active workflow screens

Governance:
- Decisions are immutable after recording
- Evidence provenance is preserved
- Athena synthesis remains advisory
- Themis remains the sole authority for governed decision recording

Validation:
- Validation Case 001 complete
- Validation Case 002 complete
- At least one contemporary non-historical thesis completed
  end-to-end

---

## Traceability Chain

Every change in Athena traces through this hierarchy.
A change is complete only when every level it affects
has been updated.

Constitutional Governance
	↓
IMS Charter
	↓
Architecture (ATHENA_ARCHITECTURE.md)
	↓
Engineering Governance
ATHENA_DEVELOPMENT_STANDARD.md
	↓
Experience Governance
UX Principles → Design System → Interface Mockup → Component Library
	↓
Implementation Plan
	↓
Code
	↓
Verification
(Did we build it correctly?)
	↓
Validation
(Did we build the right thing?)

---

## Document Authority Hierarchy

When guidance differs between project documents, the
higher-authority document governs.

Authority order:

1. IMS Charter
2. Architecture Documents
3. Development Standard
4. Design System
5. Interface Mockup
6. Component Library
7. Implementation Plan
8. Code Comments

Implementation must conform to the highest applicable authority.

If a lower-authority document conflicts with a higher-authority
document, the lower document must be updated rather than
implemented as written.

No implementation may intentionally violate a higher-authority
document without first revising that document through its
required governance process.

---

## Development Standard Amendment Rule

This document governs the engineering practices used to
implement Athena.

Amendments to this document should satisfy all of the following:

- Address a recurring development need rather than a
  one-time circumstance.
- Preserve compatibility with higher-authority documents.
- Improve clarity, consistency, governance, or reproducibility.
- Include a documented rationale in the associated architecture
  or design review.

This document should evolve deliberately and infrequently.
Project-specific implementation guidance belongs in
implementation plans rather than in the Development Standard.

When a section primarily defines architectural concepts,
the Development Standard should reference the Architecture
document rather than duplicate it. Each document owns its
topic. References are preferred over duplication.

---
