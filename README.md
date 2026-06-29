---
Document Purpose: Front door to Athena for orientation, authority framing, and repository navigation.
Authority: IMS Charter v1.0; ATHENA_ARCHITECTURE.md.
Inputs: ATHENA_ARCHITECTURE.md; ATHENA_INFORMATION_LIFECYCLE.md; ATHENA_DEVELOPMENT_STANDARD.md.
Outputs: Contributor understanding, document discoverability, and consistent terminology usage.
Updated When: Core authority relationships, operating model, or repository document map changes.
Does Not Cover: Implementation details, UI component contracts, or service-level behavior.
---

# Athena

Governed Investment Intelligence.

## What is Athena?

Athena is a governed investment intelligence platform that prepares analyst work using evidence-centric orchestration while preserving human decision authority. Its mission is to reduce mechanical workflow friction so analysts can spend more time on judgment. Its North Star is constitutionally governed, evidence-bounded, reproducible decision support. Its core philosophy is simple: intelligence may prepare and inform, but authority remains explicit, auditable, and human-governed.

## Product Identity

Athena
Governed Investment Intelligence

Athena prepares.
The analyst governs.

## How Athena Works

Athena has two complementary but independent architectural structures. The Structural Architecture defines authority - who governs what, in what order, and under what conditions. The Operational Model defines improvement - how Athena evolves through validated operational evidence. One is a hierarchy. The other is a continuous improvement loop. They do not govern each other. Confusing them is the primary source of governance drift in mature systems.

Structural Architecture:

```
IMS Charter
   ↓
Athena Architecture
   ↓
Athena Information Lifecycle
   ↓
Athena Development Standard
   ↓
Experience Architecture / Product Layer
   ↓
Agent Specifications
   ↓
Implementation
   ↓
Validation and Lessons
```

Operational Model:

```
Observe analyst work
   ↓
OVC
   ↓
First meaningful interruption
   ↓
INT
   ↓
Smallest viable change
   ↓
Validation
   ↓
Evidence
   ↓
Commit
   ↓
Repeat
```

Structural Architecture is authority.
Operational Model is improvement.
They are independent and complementary.
They do not govern each other.

## Repository Navigation

- IMS Charter: constitutional authority source for Athena.
- ATHENA_ARCHITECTURE.md: structural authority hierarchy and platform layer contracts.
- ATHENA_INFORMATION_LIFECYCLE.md: governed information lifecycle contract.
- ATHENA_DEVELOPMENT_STANDARD.md: engineering operating standard and OVC/INT improvement loop.
- ATHENA_DESIGN_SYSTEM.md: current product and UI design foundation.
- design/ATHENA_VIEW_MODEL_STANDARD.md: view model contract for experience layer rendering.
- design/ATHENA_COMPONENT_LIBRARY.md: reusable UI component contracts.
- AGENT_SPECIFICATION_STANDARD.md: canonical template for agent constitutional specifications.
- THEIA_SPECIFICATION.md: active Theia constitutional and capability specification.
- ATHENA_OPERATIONAL_EVALUATION_ENGINE.md: design principles for the Operational Evaluation Engine.
- VALIDATION_PORTFOLIO.md: portfolio-level validation coverage targets.
- VALIDATION_NOTES.md: case execution notes and observations.
- LESSONS_LEARNED.md: operational learning record.
- ATHENA_ROADMAP.md: planning direction across major milestones.

### Independent Auditor

Athena includes an Independent Auditor as a constitutional stewardship function.

- Authority: IMS Charter, Athena Architecture, Information Lifecycle, and Development Standard.
- Role: Evaluate Athena's evolution using observable evidence and report independent stewardship findings.
- Limits: Does not implement changes, does not override analyst authority, and does not create new constitutional authority.

See INDEPENDENT_AUDITOR.md for the governed standard.

## Development Vocabulary

OVC and INT are canonically defined in ATHENA_DEVELOPMENT_STANDARD.md.

OVC is Athena's operational validation mechanism for observing real analyst work and capturing the first meaningful interruption.

INT is the smallest approved implementation used to resolve one validated interruption and must be validated against the originating OVC.

README intentionally summarizes these terms and does not restate their full canonical definitions.

## Current Engineering Theme

Athena is currently in Generation IV - Analyst Readiness and Product Experience.

| Generation | Theme | Status |
|---|---|---|
| I | Constitutional Foundation | Complete |
| II | Platform Architecture | Complete |
| III | Operational Intelligence | Largely Complete |
| IV | Analyst Readiness and Product Experience | Current |

Generations are dominant engineering themes, not software release numbers.

## Quick Start

Prerequisite: install uv if needed.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Sync dependencies.

```bash
uv sync
```

2. Run Streamlit.

```bash
uv run streamlit run streamlit_app.py
```

3. Run focused tests.

```bash
.venv/bin/python -m pytest -q tests/test_workflow_assistant.py tests/test_evaluation_engine.py tests/test_evidence_discovery.py tests/test_evidence_acquisition.py tests/test_extraction_coordinator.py
```
