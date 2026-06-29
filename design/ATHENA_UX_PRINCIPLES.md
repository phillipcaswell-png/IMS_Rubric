<!-- Status: Active Standard -->

Document Authority: Versioned
Version: 1.0
Status: Frozen
Owner: Athena Product Design
Governed By: IMS Charter v1.0
Last Approved: June 2026
Purpose: Define the immutable UX principles governing the Athena Experience.
Scope: All UI decisions, component designs, layout choices, and
       interaction patterns across every Athena mode and screen.
Dependencies:
- IMS Charter v1.0
- ATHENA_DESIGN_SYSTEM.md
Supersedes: None
Superseded By:

# Athena UX Principles

## Authority

These principles are the constitutional layer of the Athena
Experience. They govern every UI decision.

A UI element that violates these principles must be redesigned
before it is implemented. A principle may only be changed through
a versioned document update with explicit rationale.

These principles do not describe visual style. They describe
why the interface is designed the way it is.

---

## The Thirteen Principles

### 1. One primary focus per screen.

Every screen answers one question and presents one primary action.
Competing focal points are a design failure, not a tradeoff.

### 2. Human-readable content always precedes system metadata.

Document names, thesis questions, and analysis content lead.
Evidence IDs, timestamps, UUIDs, and database fields follow.
The analyst came to think, not to navigate a database.

### 3. Progressive disclosure over information density.

Show what the analyst needs now.
Reveal detail only when requested.
The staging queue is collapsed. The full pillar list is hidden.
Seven pillars are never shown simultaneously.

### 4. Every constitutional action must be visually distinct.

Recording a decision, promoting evidence, and locking
a validation configuration are irreversible governed actions.
They must look different from every other interaction.
Gold. Explicit warning. Confirmation required.

### 5. Gold signifies governed authority only.

The accent color #C5A028 appears only when something
constitutional is happening or has happened.
It is not used for decoration, hover states, or emphasis.
When an analyst sees gold, they know something governed is present.
That meaning must be preserved as the platform grows.

### 6. Components never contain business logic.

Every UI component is purely presentational.
It accepts data and renders it.
It makes no database calls.
It applies no business rules.
It returns no governed artifacts.
The service layer owns logic. Components own rendering.

### 7. Every screen answers one question.

Before any screen is designed or implemented, its question
must be stated explicitly:
- Workspace: What are you doing today?
- Evidence: What have you gathered?
- Assessment: What does this pillar tell you?
- Decision: Is this decision constitutionally ready?
- Mnemosyne: What did history reveal?
If the question cannot be stated in one sentence,
the screen is trying to do too much.

### 8. Every workflow preserves evidence before judgment.

Evidence is always gathered before assessment begins.
Assessment is always complete before decision is eligible.
Decision is always recorded before historical review begins.
The interface enforces this sequence through progressive
disclosure and constitutional gates — never through trust.

### 9. Agent attribution identifies who produced information
    and what authority it carries — never omitted.

Every piece of information in the interface carries an
attribution label identifying the agent that produced it
and the authority level of that output.
Advisory content is labeled Advisory.
Governed content is labeled Governed Observation.
These labels are never omitted and never blurred.

### 10. Advisory content is always visually distinguished
     from governed content — labels never blurred.

An analyst must never have to wonder whether a passage
came from Theia's extraction (advisory) or from their own
governed observation (constitutional record).
The visual distinction between advisory and governed
is a constitutional requirement, not a stylistic choice.

### 11. Immutable actions require explicit confirmation
     and visual emphasis — never casual.

The Record Decision button is the only gold button on the
Decision screen. The immutability warning appears twice.
Confirmation is required. Escape cancels.
An action that cannot be undone must not look like one that can.

### 12. The constitutional sequence Perception → Understanding
     → Judgment → Memory is reinforced at every level.

Navigation, mode names, component labels, hero statements,
progress indicators, and agent attribution all reference
the same four-stage sequence.
The interface and the philosophy are the same thing.

### 13. The interface must reduce cognitive load,
     not simply rearrange it.

Every new UI element must either:
- clarify a decision the analyst needs to make,
- reduce effort required to complete a governed action, or
- communicate constitutional state that affects the workflow.

If a proposed element cannot satisfy at least one of these,
it must not be added. This principle is the primary guardrail
against feature creep.

---

## Application

These principles apply to:
- Every screen layout decision
- Every component design
- Every interaction pattern
- Every label and copywriting choice
- Every phase of MVP-028 implementation

When a design decision is contested, refer to these principles.
The principle governs. Opinion yields.
