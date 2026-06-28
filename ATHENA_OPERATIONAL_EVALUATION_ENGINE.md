# Operational Evaluation Engine Design Principles

The Operational Evaluation Engine is a permanent Athena subsystem.

It exists to automate evaluation preparation while preserving constitutional governance.

Every future enhancement to the engine shall conform to the following principles.

## Principle 1 — Orchestration, Not Intelligence
The engine coordinates work.

Individual services own implementation.

The engine should invoke existing services rather than duplicate their responsibilities.

## Principle 2 — Preparation Before Judgment
The engine prepares evaluations.

It never performs governed analyst work.

Its terminal state is:

**Ready for Analyst**

The analyst remains solely responsible for:

- evidence promotion
- governed assessments
- analyst rationale
- confidence basis
- falsification triggers
- investment decisions

## Principle 3 — Idempotent Execution
Preparation is repeatable.

Repeated requests for the same:

- ticker
- observation date

shall converge on the same evaluation unless an explicit future force-new option is requested.

Repeated execution improves preparation rather than creating duplicate work.

## Principle 4 — Honest State
The engine shall expose truthful preparation status.

Unknown is never reported as complete.

Unavailable is never reported as successful.

Partial preparation is a valid operational state.

Preparation Fidelity is mandatory.

## Principle 5 — Durable Orchestration
Engine state shall survive application restarts whenever practical.

Preparation progress is part of the product, not temporary runtime state.

## Principle 6 — Single Source of Truth
The engine shall expose one structured preparation status model.

That same model shall be reused by:

- REST API
- Streamlit UI
- CLI
- telemetry
- automated tests
- logs
- future background workers

No client shall invent or reinterpret preparation state.

The engine is the authoritative source of evaluation progress.

## Principle 7 — Progressive Automation
Automation should deepen preparation rather than expand authority.

Future work should increase Athena's ability to prepare evaluations without reducing analyst responsibility.

Each sprint should answer:

"What repetitive analyst work disappeared?"

## Principle 8 — Engine-First Architecture
The Operational Evaluation Engine is Athena's execution layer.

Clients invoke the engine.

Clients do not recreate orchestration.

Expected clients include:

- Streamlit
- REST API
- CLI
- automated tests
- scheduled jobs
- future automation agents

The UI is a client of the engine, not the owner of the workflow.

## Principle 9 — Constitutional Compliance
If a future enhancement would require Athena to:

- determine governed scores
- approve evidence
- write analyst reasoning
- determine investment decisions

the enhancement belongs outside the Operational Evaluation Engine.

The constitutional boundary remains:

Athena prepares.

The analyst governs.

## Long-Term Objective
Every future capability should move Athena closer to this workflow:

Ticker

↓

Observation Date

↓

Operational Evaluation Engine

↓

Ready for Analyst

↓

Analyst Review

↓

Governed Decision

↓

Historical Learning

The engine's purpose is complete when analysts spend their time evaluating businesses rather than assembling evaluations.