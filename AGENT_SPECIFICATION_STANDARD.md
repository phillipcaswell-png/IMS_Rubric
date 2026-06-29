---
Document Purpose: Define the required structure and constitutional constraints for all Athena agent specifications.
Authority: IMS Charter v1.0; ATHENA_ARCHITECTURE.md.
Inputs: IMS Charter v1.0; ATHENA_ARCHITECTURE.md; ATHENA_INFORMATION_LIFECYCLE.md.
Outputs: Agent specifications such as THEIA_SPECIFICATION.md.
Updated When: Agent governance template or mandatory constitutional constraints change.
Does Not Cover: Individual agent capability behavior details or implementation internals.
---

# Agent Specification Standard

## Purpose
Defines the constitutional template every agent specification must follow before implementation.

## Required Sections
- Constitutional Position
- Constitutional Authority
- Mission
- Responsibilities
- Explicit Prohibitions
- Non-Goals
- Trust Model
- Read Permissions
- Write Permissions
- Prohibited Writes
- Inputs and Surfaces
- Governance Constraints
- Failure Philosophy
- Audit Expectations
- Capability Model
- Capability Registry
- Capability Maturity Model
- Validation Requirements
- Implementation Mapping
- Change Control

## Constitutional Position
State the single constitutional responsibility the agent holds.

## Constitutional Authority
Identify the governing documents from which the agent derives authority.

At minimum specify:
- Constitutional authority source
- Engineering authority source
- Specification authority source

An agent may never derive authority from its implementation.

## Mission
State what the agent is responsible for making possible and what authority it does not hold.

## Responsibilities
State what the agent is permitted to do using active verbs such as discover, stage, surface, coordinate, and observe.

## Explicit Prohibitions
State what the agent must never do. Specifications must include these prohibitions:
- Must never score
- Must never recommend
- Must never promote
- Must never write governed records
- Must never override analyst judgment
- Must never bypass constitutional gates

## Non-Goals
State capabilities intentionally excluded from the current specification version.

## Trust Model
Declare whether outputs are advisory, governed, or mixed with explicit boundaries.

## Read Permissions
Tables and records the agent may observe.

## Write Permissions
Tables and records the agent may modify.

## Prohibited Writes
Tables and records this agent must never modify.

## Inputs and Surfaces
Describe what the agent observes and what it surfaces to analysts or other agents.

## Governance Constraints
List constitutional prohibitions and escalation boundaries.

## Failure Philosophy
When an agent cannot perform its function:

- Governed workflows continue.
- Analyst authority increases.
- No constitutional boundary may be bypassed.
- Failure must degrade gracefully rather than silently.

## Audit Expectations
Define what must be logged, what must never be logged, and retention expectations.

## Capability Model
Every agent capability is implemented as either:
- A Core enhancement, or
- A named Capability

Capabilities are technology-neutral constitutional extension points.
They may be implemented by rules, models, or remote services.
In user-facing contexts, Capabilities may be presented as Skills.

Capability Rules:
- Must declare a single constitutional responsibility
- Must state what it observes and what it surfaces
- Must produce no governed output independently
- Must inherit all constitutional constraints of its parent agent
- Must be registered in the agent specification before implementation

## Capability Registry
Each capability entry must include:
- Capability name
- Purpose
- Inputs
- Surfaces
- UI/Surface name
- Status
- Maturity level
- Target MVP or TBD

## Capability Maturity Model
Level 0 — Proposed: Architecture approved, no implementation
Level 1 — Experimental: Implemented, not used in governed validation
Level 2 — Validated: Exercised against historical validation cases
Level 3 — Constitutional: Repeatable value demonstrated, future changes require constitutional review

Maturity does not expand constitutional authority.
All capabilities inherit agent constraints regardless of maturity level.
A capability advances in maturity only after successful validation
against real historical cases reviewed by an analyst.

## Validation Requirements
Describe case-driven validation gates required before maturity advancement.

## Implementation Mapping
Map each core enhancement or capability to an MVP or implementation track.

## Change Control
The following changes require constitutional review before implementation:

- Constitutional authority
- Mission
- Responsibilities
- Explicit prohibitions
- Trust model
- State ownership
- Capability maturity promotion to Level 3

Implementation details may evolve without constitutional review provided they do not alter constitutional behavior.

## Related Documents

- README.md
- ATHENA_ARCHITECTURE.md
- ATHENA_INFORMATION_LIFECYCLE.md
- ATHENA_DEVELOPMENT_STANDARD.md
- THEIA_SPECIFICATION.md
