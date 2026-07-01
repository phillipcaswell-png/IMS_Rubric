---
Document Purpose: Establish the canonical operating authority and constitutional boundaries for Hermes v0.
Authority: IMS Charter v1.0; ATHENA_ARCHITECTURE.md; ATHENA_INFORMATION_LIFECYCLE.md; ATHENA_DEVELOPMENT_STANDARD.md.
Inputs: Athena constitutional and structural governance artifacts; Hermes v0 planning artifacts.
Outputs: Binding Hermes v0 authority boundary, lifecycle gate, and review criteria.
Updated When: Constitutional governance review approves changes to Hermes authority, boundaries, or lifecycle gates.
Does Not Cover: Hermes implementation details, migrations, scheduler configuration, test plans, or service deployment instructions.
---

# Hermes Operating Contract
## Canonical Operating Contract v0

## 1. Canonical Status
`HERMES_OPERATING_CONTRACT.md` is the canonical source of truth for Hermes v0.

Implementation must conform to this Operating Contract. This contract does not conform to implementation convenience.

If implementation guidance conflicts with constitutional governance, the constitutional hierarchy prevails.

No implementation, implementation review, operational validation activity, or future evolution may override authority established by this Operating Contract. Constitutional authority may only change through formal amendment of this contract.

## 2. Source Hierarchy
Hermes v0 authority and interpretation order:

1. Athena Constitution, where applicable
2. Athena Architecture
3. `ATHENA_ENGINEERING_LIFECYCLE.md`
4. `ATHENA_DEVELOPMENT_STANDARD.md`
5. Hermes.docx, Hermes v0 Implementation Specification
6. Hermes v0 30-Day Operational Validation document

Current repository fallback:
- `ATHENA_ENGINEERING_LIFECYCLE.md` is not yet present in this repository.
- Lifecycle governance for Hermes is therefore derived from `ATHENA_DEVELOPMENT_STANDARD.md` and the structural hierarchy in `ATHENA_ARCHITECTURE.md`.
- `ATHENA_ENGINEERING_LIFECYCLE.md` is a planned governed artifact and becomes authoritative lifecycle reference when established.
- No unsupported lifecycle structures are authorized in this contract.

## 3. Engineering Lifecycle Position
Hermes is currently in the Operating Contract phase.

Required sequence:

1. Operating Contract
2. Implementation Specification
3. Implementation
4. Independent Review
5. Operational Validation
6. Future Constitutional Evolution

Hermes implementation may not begin until this Operating Contract is independently reviewed and accepted.

## 4. Constitutional Success Condition
Hermes succeeds by executing deterministic operational work while remaining constitutionally incapable of performing analyst or reasoning responsibilities. Correct architectural restraint is more important than feature count.

## 5. Constitutional Position
Hermes is:
- Athena's deterministic operations service
- Not a reasoning agent
- Not a constitutional peer to Theia
- Not an analyst
- Not an investment decision system
- Not a governed decision-making component

Hermes exists only to perform deterministic operational work.

## 6. Authority Chain
```text
Data Sources
      |
      v
Hermes
(find, detect, retrieve, measure, log, queue)
      |
      v
Athena
(store, organize, govern)
      |
      v
Theia
(reason, synthesize, evaluate)
      |
      v
Analyst
(decide, approve, publish)
```

**Clarification:** This diagram represents information flow only. Constitutional authority remains with the Analyst. Theia provides reasoning support but does not supersede analyst judgment.

Hermes has no authority over governed artifacts and no authority over analyst judgment.

## 7. Constitutional Guardrail Statement
Hermes may observe, detect, measure, log, and queue work items. Hermes shall not interpret evidence, modify Knowledge Records, alter assessments, change scores, or update governed artifacts.

## 8. Allowed Responsibilities
Hermes may only:
- observe
- detect
- retrieve external source material solely for deterministic operational inspection (for example, hashing, parsing, and change detection). Hermes shall not stage, promote, classify, or introduce evidence into Athena's governed evidence lifecycle.
- measure
- hash
- parse
- validate deterministic conditions
- log
- queue work items

No additional operational authority may be inferred.

## 9. Constitutional Prohibitions
Hermes shall never:
- reason
- interpret evidence
- summarize evidence
- synthesize evidence
- score
- rank
- prioritize
- estimate confidence
- estimate probability
- estimate risk
- estimate materiality
- estimate valuation
- estimate investment impact
- estimate score impact
- determine importance
- determine business significance
- determine analyst priority
- determine portfolio priority
- make investment decisions
- make governance decisions
- modify Knowledge Records
- modify assessments
- modify governed artifacts
- expand its own authority

Hermes shall never make decisions based upon:
- materiality
- importance
- investment impact
- valuation impact
- score impact
- business significance
- analyst priority
- portfolio priority
- risk significance

Hermes may detect that a deterministic trigger occurred. Hermes shall never determine whether that trigger is important, material, investment-relevant, valuation-relevant, score-relevant, or worthy of analyst attention. Those judgments belong exclusively to governed Athena reasoning and the human analyst.

Creation of a Hermes work item represents operational observation only. A work item is not a recommendation, escalation, investment opinion, governance decision, or analyst instruction.

## 10. Deterministic Rule Integrity
Hermes operates only from closed deterministic trigger conditions.

If a trigger is not explicitly authorized by this Operating Contract, Hermes shall not create a work item.

Explicitly prohibited:
- heuristic prioritization
- adaptive polling
- dynamic scheduling based on previous observations
- confidence scoring
- probability thresholds
- inferred materiality
- inferred importance
- inferred urgency
- selective source skipping
- hidden ranking logic

Permitted deterministic conditions include objective operational facts only, such as:
- hash changed
- source unavailable
- configured review interval exceeded
- parse succeeded
- parse failed
- configured cost ceiling reached
- explicitly configured deterministic thresholds

## 11. Repository Write Boundary
Approved Hermes write targets are operational tables only:
- `hermes_cycles`
- `hermes_work_items`
- `hermes_non_escalation_samples`

Everything outside approved Hermes write targets is constitutionally prohibited.

Hermes shall not modify governed Athena artifacts outside authorized Hermes operational tables.

## 12. Database Security Boundary
Hermes authority must be enforced by database permissions, not application intent.

Hermes v0 is incomplete until raw database evidence proves:
- permitted SELECT operations
- permitted INSERT operations
- denied UPDATE operations
- denied DELETE operations
- denied ALTER operations
- denied DROP operations

Migration files, ORM definitions, configuration, or application code are insufficient evidence.

Every denied privilege must be demonstrated by an attempted database operation with captured raw output.

## 13. Evidence Sufficiency Standard
Every implementation claim requires objective evidence, including examples such as:
- `git diff`
- migration output
- scheduler output
- permission verification output
- test results
- database output

Claims without supporting evidence fail review.

## 14. Repository Boundary Verification
Independent review must verify no files outside approved Hermes implementation scope were modified.

Unexpected repository changes are review failure unless explicitly authorized.

## 15. Review Decision Matrix
Permitted review outcomes:
- Accepted: all constitutional and operational gates passed
- Accepted with Minor Follow-up: only operational issues remain and constitutional boundaries are intact
- Fix Pass Required: one or more review gates failed and re-validation is required
- Blocked: constitutional boundary violation or unresolved completion gate

## 16. Hard Completion Gate
Hermes v0 is incomplete until all are true:
- implementation is complete
- deterministic rule integrity is verified
- repository boundaries are preserved
- database permissions are verified with raw evidence
- independent review passes
- constitutional compliance is confirmed

Self-attestation is not accepted.

Any implementation that exceeds authority established by this Operating Contract constitutes a constitutional failure regardless of functional correctness.

## 17. Operational Validation Requirement
Hermes 30-Day Operational Validation is a mandatory Engineering Lifecycle phase.

Operational validation rules:
- operational validation is mandatory
- Hermes shall not expand scope during operational validation
- validation verifies the current contract
- validation does not redesign the current contract
- every failure must be logged with deterministic cause traceable to a defined contract condition

The operational validation framework is defined in `HERMES_30_DAY_OPERATIONAL_VALIDATION.md`. Until that governed artifact exists, operational validation shall follow the approved Hermes v0 validation specification. Upon creation, the governed validation document becomes the authoritative lifecycle reference for operational validation.

## 18. Evolution Backlog Separation
Deferred and unauthorized for Hermes v0:
- Olympus
- Benchmark Mode
- local reasoning
- frontier reasoning
- notification services
- dashboards
- expanded SEC ingestion
- multi-company execution
- continuous work queues

Presence in planning artifacts does not authorize implementation.

## 19. Contract Gate
Hermes remains constitutionally blocked for implementation until this Operating Contract is independently reviewed and accepted.

## 20. Constitutional Amendment
Hermes authority may only be expanded through formal amendment of this Operating Contract followed by implementation, independent review, and operational validation. No implementation artifact, implementation convenience, or operational practice may implicitly expand Hermes authority.
