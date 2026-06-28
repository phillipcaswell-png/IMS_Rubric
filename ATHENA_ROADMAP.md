v1.0.0 — Constitutional Baseline (complete)
  ↓
MVP-019 — Service Layer Consolidation
  (internal architecture only, no functional changes)
  ↓
MVP-019 Verification — Validation Case 001 regression
  ↓
MVP-019B — Input Layer & Analyst Experience
  (validated UX improvements only)
  ↓
MVP-019B Verification — Validation Case 001 spot checks
  ↓
MVP-020 — Athena Orchestration
  ↓
MVP-021 — Historical Validation Expansion

Objective:
Expand validation beyond a single historical case by defining and operationalizing the Validation Portfolio for constitutional stress coverage across diverse thesis contexts.

Success Criteria:
1. Validation Portfolio document exists with explicit coverage targets and planned case categories.
2. Coverage Vector template is defined for each planned case.
3. Validation Case 001 remains active and documented as current baseline coverage.
4. MVP-021 documentation clearly separates objectives from non-objectives.
5. Roadmap references Validation Portfolio as the governing expansion artifact.

Non-objectives:
- No change to constitutional gates or decision authority.
- No change to governed scoring or decision record schema.
- No automatic case generation or autonomous governed execution.
- No rewrite of prior validation notes.

Validation Portfolio Reference:
See VALIDATION_PORTFOLIO.md for portfolio scope, current coverage, planned expansion categories, and coverage vector structure.

## MVP-032 — Operational Evaluation Engine Foundation

Generation III — Phase 6 Automation.
Stable baseline required: `1cbb471` or later.
Design specification: MVP-032_DESIGN.md

Purpose:
Establish the first durable orchestration layer for evaluation preparation.

Sprint 1 creates an engine foundation that can prepare an evaluation shell to a truthful Ready for Analyst state without performing governed analyst judgment.

Frozen Sprint 1 scope:
- engine skeleton
- lifecycle model
- structured preparation status
- durable persistence approach
- idempotent evaluation lookup
- REST delegation contract
- Ready for Analyst shell
- Preparation Fidelity validation

Sprint 1 non-goals:
- autonomous evidence acquisition
- autonomous promotion
- scoring
- analyst rationale
- investment decisions
- UI redesign
- speculative AI reasoning

## MVP-034 — Analytical Visualization

Generation III capability.
Requires stable v2.0 foundation before implementation begins.
Design specification: design/ATHENA_ANALYTICAL_VISUALIZATION.md

Purpose:
Transform governed data into analytical instruments that make
Athena's reasoning immediately visible and explorable.

These are not AI features. They are analytical instruments
built from governed data. Generation III intelligence powers
them but their purpose is analysis.

Visualization Catalog:

1. Risk/Reward Quadrant
  Configurable axes chosen by the analyst.
  Examples: Risk/Return, Confidence/CAGR,
  Evidence Strength/Strategic Importance,
  Margin of Safety/Business Quality,
  Historical Accuracy/Framework Confidence.

2. Evidence Landscape
  Interactive. X: Evidence Strength. Y: Strategic Importance.
  Clicking a theme illuminates supporting evidence cards.

3. Confidence Cone
  Predicted confidence band at decision time.
  Compared against actual outcome by Mnemosyne.
  Calibration instrument — measures framework accuracy
  across the portfolio, not individual thesis performance.

4. Scenario Projection
  Bull, Base, Bear trajectories as confidence bands.
  Tied to analyst assumptions and falsification triggers.
  Updates when assumptions change.

5. Thesis Trajectory
  Evolution of conviction over time.
  Each point represents evidence completeness, confidence,
  thesis quality, and valuation attractiveness at that moment.
  Hover opens: evidence added, analyst notes, pillar score
  changes, review outcomes.
  No investment software presents conviction evolution this way.

6. Outcome Attribution Timeline
  Visual Mnemosyne review history.
  Decision → 1Y → 3Y → 5Y with attribution types.

7. Portfolio Position Map
  All theses in governed state space simultaneously.

8. Decision Surface
  Contour plot showing the decision space.
  X: Business Quality. Y: Margin of Safety.
  Color: Expected Outcome.
  Current thesis appears as a point on the surface.
  As assumptions change, the point moves.
  Shows how close a thesis is to crossing a decision boundary.
  Complements the Confidence Cone by explaining why a
  recommendation changes, not just how uncertainty evolves.

9. Framework Calibration Dashboard
  Portfolio-level. For Athena itself, not individual theses.
  Powered by Mnemosyne after sufficient completed validations.
  Answers: How often did Bull scenarios occur? Were confidence
  intervals well calibrated? Which pillars most often preceded
  successful outcomes? Which falsification triggers were most
  predictive? Where does the framework systematically underperform?
  Mnemosyne becomes a governed feedback mechanism for improving
  the framework while preserving immutable historical decisions.

Constitutional constraint for all visualizations:
- Governed data only
- No visualization generates governed artifacts
- Confidence Cone comparison is advisory only
- Framework Calibration Dashboard is observational only
- No visualization modifies any historical decision record
