Document Authority: Versioned
Governed By: IMS Charter v1.0; ATHENA_ARCHITECTURE.md; ATHENA_OPERATIONAL_EVALUATION_ENGINE.md
Document Owner: Athena Architecture
Current Version: 1.0
Status: Design Freeze
Effective Date: June 2026
Purpose: Freeze the Sprint 1 implementation contract for the Operational Evaluation Engine foundation.
Scope: Sprint 1 design only. Defines orchestration foundation, truthful preparation state, durability, idempotency, and validation boundaries. Excludes production implementation detail beyond the frozen contract.
Implements Charter Principles: 1, 3, 5
May Modify: Sprint 1 Operational Evaluation Engine design boundaries, status contract, lifecycle definition, and validation expectations for MVP-032 only.
May Not Modify: Constitutional governance responsibilities, analyst authority, governed scoring, evidence promotion authority, decision authority, audit semantics, or higher-order architecture documents.
Dependencies:
- IMS Charter v1.0
- ATHENA_ARCHITECTURE.md
- ATHENA_OPERATIONAL_EVALUATION_ENGINE.md
- ATHENA_DEVELOPMENT_STANDARD.md
Supersedes: None
Superseded By:

# MVP-032 — Operational Evaluation Engine Foundation

## 1. Metadata

This document is the frozen Sprint 1 implementation contract for the Operational Evaluation Engine.

It answers four questions only:

- Why this sprint exists
- What Sprint 1 builds
- What Sprint 1 intentionally defers
- How Sprint 1 success is measured

Anything outside those questions belongs in higher-order architecture, later sprint designs, or implementation artifacts.

---

## 2. Sprint Identity

Title:

MVP-032 — Operational Evaluation Engine Foundation

Classification:

Generation III — Phase 6 Automation

Purpose:

Establish the first durable orchestration layer capable of preparing evaluations to a truthful Ready for Analyst state without performing governed analyst judgment.

---

## 3. Product Problem

Athena already supports governed evaluation.

The analyst can stage evidence, complete governed assessment fields, record decisions, and perform historical review inside a constitutionally bounded workflow.

The remaining productivity bottleneck is evaluation preparation.

Preparation work still depends on manual initiation, manual coordination, and manual reconstruction of evaluation state before governed analysis begins.

Sprint 1 exists to reduce preparation effort without changing who holds judgment authority.

It begins Automation by creating a durable execution layer that can prepare an evaluation shell truthfully and repeatably.

Sprint 1 does not attempt to complete the evaluation.

It makes evaluation preparation operational.

---

## 4. Constitutional Boundary

Athena prepares.

The analyst governs.

Permitted Sprint 1 preparation activities:

- create or resume a preparation record for a ticker and observation date
- coordinate existing preparation services through one engine entry point
- assemble and persist truthful preparation state
- report readiness, incompleteness, unavailability, and failure honestly
- prepare an evaluation shell that is ready for analyst review
- expose preparation status to clients through one canonical model

Prohibited Sprint 1 activities:

- governed evidence promotion
- governed assessment scoring
- analyst rationale generation
- confidence basis generation
- falsification trigger generation
- investment recommendation or decision generation
- approval of evidence quality or analytical sufficiency
- speculative AI reasoning presented as governed output

No analyst authority shall be automated.

---

## 5. Sprint Scope

Sprint 1 builds only the minimum durable foundation required to operationalize preparation.

Included deliverables:

- engine skeleton
- lifecycle model
- structured preparation status
- durable persistence approach
- idempotent evaluation lookup
- REST delegation contract
- Ready for Analyst shell
- Preparation Fidelity rules
- validation approach

Sprint 1 implementation boundary:

- one engine-owned orchestration entry point
- one canonical preparation status model
- one durable record keyed by ticker and observation date
- truthful lifecycle state transitions
- thin client adapters that delegate rather than orchestrate

Explicitly excluded from Sprint 1:

- autonomous evidence acquisition
- autonomous promotion
- scoring
- analyst rationale
- investment decisions
- UI redesign
- speculative AI reasoning
- background worker architecture
- multi-stage automation planning beyond the Sprint 1 lifecycle

---

## 6. Lifecycle

Sprint 1 defines a minimal truthful lifecycle.

Lifecycle states:

1. Requested
2. Preparing
3. Partially Prepared
4. Ready for Analyst
5. Failed

Lifecycle intent:

- Requested means a preparation request has been accepted and a durable preparation record exists.
- Preparing means orchestration is actively coordinating preparation work.
- Partially Prepared means some required preparation outputs exist, but the engine cannot truthfully claim readiness.
- Ready for Analyst means the evaluation shell is operationally ready for analyst review.
- Failed means the engine cannot continue without intervention and must report why.

Sprint 1 lifecycle constraints:

- Unknown work may not be collapsed into Ready for Analyst.
- Missing required preparation outputs may not be collapsed into success.
- Failed and Partially Prepared are both valid end states for a given run.
- Richer sub-stages, retries, recovery classes, and background progression are explicitly deferred.

Future increments may introduce finer-grained lifecycle stages, but Sprint 1 must not claim capabilities it does not implement.

---

## 7. Ready for Analyst

Sprint 1 defines Ready for Analyst as an operational readiness state, not an evaluation-complete state.

Ready for Analyst means:

- the evaluation record exists
- the preparation record exists durably
- the engine has completed Sprint 1 preparation steps truthfully
- clients can open the evaluation and inspect preparation state through the canonical status model
- remaining work is governed analyst work rather than missing orchestration work

Ready for Analyst does not mean:

- evidence is fully sufficient
- promoted evidence has been approved by Athena
- governed assessments are complete
- a decision is ready to record
- historical learning is complete

Sprint 1 readiness marks handoff to the analyst, not completion of the investment workflow.

---

## 8. Idempotency

Idempotency is a product requirement.

Repeated requests for the same ticker and observation date shall converge on one preparation record unless a future governed design explicitly introduces a force-new option.

Sprint 1 idempotency rules:

- the engine must resolve duplicate requests to the same preparation record
- repeated execution should improve or resume preparation rather than duplicate it
- clients must receive the current canonical status for that record
- the engine must not create duplicate evaluation shells for the same request key under normal operation

Idempotency exists to make preparation reliable, recoverable, and safe to invoke from multiple clients.

---

## 9. Preparation Fidelity

Preparation Fidelity is mandatory.

Sprint 1 shall report preparation truthfully.

Mandatory rules:

- Unknown is never Complete.
- Unavailable is never Successful.
- Partial preparation is valid.
- Failure must remain visible.
- Readiness claims require affirmative evidence from the engine's own tracked steps.

Preparation reporting is part of the product.

Sprint 1 succeeds only if the engine's status can be trusted more than ad hoc client inference.

---

## 10. Structured Status Model

Sprint 1 defines one canonical preparation status object.

The same structure shall be reused by:

- REST
- UI
- tests
- logs
- CLI
- future workers

The Operational Evaluation Engine is the single source of truth for preparation state.

Minimum canonical status contract:

```
{
  "request_key": {
    "ticker": str,
    "observed_on": str
  },
  "evaluation_id": int | null,
  "state": "Requested" | "Preparing" | "Partially Prepared" | "Ready for Analyst" | "Failed",
  "ready_for_analyst": bool,
  "preparation_fidelity": "Truthful",
  "step_status": {
    "evaluation_shell": "Pending" | "Complete" | "Failed",
    "persistence": "Pending" | "Complete" | "Failed",
    "status_publication": "Pending" | "Complete" | "Failed"
  },
  "messages": [str],
  "blocking_issues": [str],
  "updated_at": str,
  "created_at": str
}
```

Sprint 1 contract rules:

- clients may display or transport this object
- clients may not reinterpret lifecycle meaning
- clients may not synthesize readiness independently
- additional fields may be appended in future versions, but Sprint 1 fields define the minimum contract

---

## 11. API Contract

Sprint 1 defines an engine-first API shape.

The REST endpoint remains a thin adapter.

All orchestration belongs to the engine.

Sprint 1 intended contract:

- request preparation for a ticker and observation date
- receive the canonical preparation status object
- request current status for an existing preparation record
- never duplicate orchestration logic in the REST layer

REST responsibilities:

- validate request shape
- invoke the engine
- return the canonical engine response
- map transport errors without redefining engine state

REST non-responsibilities:

- lifecycle ownership
- preparation inference
- duplicate recovery logic
- readiness calculation

The same delegation rule applies to Streamlit, CLI, tests, and future automation clients.

---

## 12. Persistence

Sprint 1 shall use the simplest durable persistence compatible with the current architecture.

Persistence objective:

- preserve preparation progress across application restarts whenever practical

Sprint 1 persistence design:

- a durable preparation record stored in the current application persistence layer
- keyed by ticker and observation date through an idempotent lookup path
- storing lifecycle state, canonical status payload, timestamps, and failure visibility

Sprint 1 persistence constraints:

- no speculative platform redesign
- no distributed workflow assumptions
- no background queue dependency
- no client-owned state as the source of truth

Sprint 1 persists orchestration progress because preparation state is product state, not temporary runtime state.

---

## 13. Validation

Sprint 1 must be accepted through repeatable, measurable checks.

Acceptance criteria:

1. A request for a ticker and observation date creates or resumes one durable preparation record.
2. Repeating the same request does not create duplicate preparation records.
3. The engine exposes one canonical preparation status object.
4. REST returns the engine's status object without recreating orchestration.
5. Preparation state survives application restart.
6. Ready for Analyst is reported only when Sprint 1 preparation requirements are satisfied.
7. Partial preparation is reported truthfully when readiness is not achieved.
8. Failure is reported truthfully when preparation cannot continue.
9. No governed scoring, promotion, rationale, or decision authority is automated.
10. Existing analyst workspace governance remains unchanged.

Validation evidence may include:

- automated tests for idempotent lookup and lifecycle truthfulness
- restart verification for durable status persistence
- transport-level verification for REST delegation behavior
- regression checks confirming no constitutional authority expansion

---

## 14. Non-Goals

Sprint 1 intentionally defers the following work to later automation sprints:

- autonomous evidence retrieval
- autonomous evidence staging
- autonomous evidence promotion
- automated observation generation
- governed score suggestion
- analyst rationale drafting
- confidence estimation
- falsification trigger generation
- investment decision support beyond truthful readiness state
- UI redesign for automation-native workflows
- advanced lifecycle planning, retries, or scheduling frameworks
- speculative agentic behavior presented as engine capability

These deferrals are intentional.

Sprint 1 exists to establish durable orchestration foundation before capability expansion.

---

## 15. Success Definition

Sprint 1 succeeds when Athena possesses a durable, idempotent, testable orchestration foundation capable of preparing an evaluation shell to a truthful Ready for Analyst state while preserving constitutional governance.

That success is achieved only if:

- the engine becomes the authoritative source of preparation state
- clients delegate orchestration rather than recreate it
- readiness is truthful
- preparation survives restart
- repeated invocation converges on one preparation record
- analyst authority remains unchanged

This document is the frozen implementation contract for MVP-032 and remains stable throughout Sprint 1 unless formally revised.