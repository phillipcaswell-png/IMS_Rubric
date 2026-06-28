# Athena Platform Architecture

## Constitutional Authority
- IMS Charter v1.0 is the supreme governing document.
- All Athena architecture derives authority from the Charter.
- Analyst judgment remains the constitutional authority for governed investment decisions.
- AI agents are advisory, coordinating, or supportive only unless explicitly granted governed authority by a higher constitutional document.

## Platform Layers
- Layer 1 — Constitution
    - IMS Charter v1.0
    - GOVERNANCE_NOTES.md
- Layer 2 — Engineering Standard
    - ATHENA_ARCHITECTURE.md
    - ATHENA_DEVELOPMENT_STANDARD.md
    - AGENT_SPECIFICATION_STANDARD.md
    - ATHENA_OPERATIONAL_EVALUATION_ENGINE.md
- Layer 3 — Agent Specifications
    - THEIA_SPECIFICATION.md — Evidence perception and discovery
    - THEMIS_SPECIFICATION.md — Constitutional governance (future)
    - HERMES_SPECIFICATION.md — Workflow coordination (future)
    - MNEMOSYNE_SPECIFICATION.md — Historical learning (future)
- Layer 4 — MVP Design Containers
    - MVP-023_DESIGN.md through MVP-026_DESIGN.md
- Layer 5 — Implementation
    - services.py — governed business logic
    - streamlit_app.py — presentation and orchestration
- Layer 6 — Validation and Evidence
    - VALIDATION_PORTFOLIO.md
    - VALIDATION_NOTES.md
    - LESSONS_LEARNED.md
    - CALIBRATION_REPORT.md (future)

## Authority Chain
If two documents conflict, the higher document in the authority chain governs.

IMS Charter v1.0
↓
GOVERNANCE_NOTES.md
↓
ATHENA_ARCHITECTURE.md
↓
ATHENA_DEVELOPMENT_STANDARD.md / AGENT_SPECIFICATION_STANDARD.md
↓
Agent Specifications
↓
MVP Design Containers
↓
Implementation Files
↓
Validation Records and Lessons Learned

## Agent Operating Principle
- Every agent owns exactly one constitutional responsibility.
- Agents may observe, coordinate, stage, or suggest.
- Agents may not decide, score, recommend, promote, or create governed records unless explicitly authorized by the applicable agent specification and higher authority.
- Analyst authority remains primary.

## Athena Responsibilities
Athena owns platform orchestration, not delegated agent responsibilities.

Athena owns:
- Session orchestration
- Cross-agent coordination
- Analyst briefing
- Workflow initiation
- Platform-level context assembly
- System-level continuity across agents
- Operational evaluation preparation through the Operational Evaluation Engine

Athena delegates:
- Evidence perception and discovery to Theia
- Constitutional governance and decision gates to Themis
- Workflow coordination and reminders to Hermes
- Historical learning and outcome review to Mnemosyne

## Development Sequence
Constitution -> Architecture -> Engineering Standard -> Agent Specification -> MVP Design Container -> Implementation -> Validation -> Evidence -> Evolution

## Future Documents
- THEMIS_SPECIFICATION.md, HERMES_SPECIFICATION.md, and MNEMOSYNE_SPECIFICATION.md are future documents.
- They are referenced here but must not be created until each agent is ready for formal design.
- ATHENA_OPERATIONAL_EVALUATION_ENGINE.md defines the permanent engine-first preparation boundary for evaluation orchestration.
- ATHENA_GLOSSARY.md is deferred until after Validation Case 003, when terminology has stabilized across multiple validation cases and agent specifications.
