<!-- Status: Future Placeholder -->

Document Authority: Versioned
Version: 1.0
Status: Design Frozen
Owner: Athena Product Design
Governed By: IMS Charter v1.0
Last Approved: June 2026
Purpose: Define the analytical visualization language for Athena.
Scope: Visualization philosophy, governed constraints, interaction
       principles, chart grammar, color semantics, animation rules,
       accessibility requirements, and the nine-visualization catalog.
       Implementation reference for MVP-034.
May Modify: UI presentation layer only.
May Not Modify: Constitutional architecture, service layer, agent
                responsibilities, governed workflow behavior, or
                any historical decision record.
Dependencies:
- IMS Charter v1.0
- ATHENA_ARCHITECTURE.md
- ATHENA_DESIGN_SYSTEM.md
- ATHENA_UX_PRINCIPLES.md
Supersedes: None
Superseded By:

# Athena Analytical Visualization

## Philosophy

Athena's visualizations are analytical instruments, not
decorative charts.

Every visualization:
- Renders governed data only
- Generates no governed artifacts
- Serves one analytical question
- Operates within the constitutional model

Generation III intelligence powers these instruments.
Their purpose is analyst understanding, not AI demonstration.

The most important visualization in Athena is not the most
visually complex one. It is the one that most clearly answers
the question the analyst is asking right now.

---

## Governed Constraints

Every visualization must satisfy all of the following:

- Reads only from governed tables or governed service functions
- Writes nothing to any table or session state
- Never modifies a historical decision record
- Never creates an observation, score, or governed artifact
- Clearly distinguishes advisory data from governed data
- Degrades gracefully when data is insufficient

The Confidence Cone and Framework Calibration Dashboard are
advisory instruments. They inform framework evolution but
never trigger it automatically. Framework changes require
the governed process defined in ATHENA_DEVELOPMENT_STANDARD.md.

---

## Interaction Principles

- Hover reveals detail
- Click explores related governed content
- No interaction triggers a governed action
- No interaction writes data
- Configurable axes follow analyst intent
- All interactions are reversible without consequence

---

## Standard Chart Grammar

Points represent governed events or states.
Bands represent uncertainty or confidence ranges.
Trajectories represent evolution over time.
Surfaces represent decision spaces.
Color communicates constitutional state.

Every data point must be traceable to its governed source.
Hovering any point must surface the originating evidence,
observation, or decision record.

---

## Color Semantics

Gold (#C5A028)
  Governed authority. Constitutional milestone.
  Active thesis. Current position on surface.

Green (#2E7D52)
  Confirmed. Promoted. Complete. Positive outcome.
  Inside predicted confidence band.

Amber (#8B6914)
  Pending. Advisory. Analyst attention required.
  Approaching decision boundary.

Red (#7D2E2E)
  Constitutional block. Regime change signal.
  Outside predicted confidence band. Bear scenario.

White (#E8E6E0)
  Neutral analytical content.
  Background data points. Secondary information.

Secondary (#8B8B9A)
  Metadata. Axis labels. Supporting context.

Color is never the sole carrier of meaning.
Every color-coded element includes a text label or tooltip.

---

## Animation Rules

Trajectory evolution: 300ms per point, ease-in-out.
Cone narrowing: reflects evidence accumulation, 200ms.
Decision surface update: 150ms when assumptions change.
Portfolio position movement: 200ms when filters change.

No decorative animation.
No looping animation.
No animation that delays analyst access to data.

---

## Accessibility Requirements

- Color never the sole indicator of meaning
- All charts keyboard navigable
- Screen reader labels on all data points
- Minimum contrast ratio 4.5:1 for all text
- Focus ring visible on all interactive elements
- All visualizations usable without mouse

---

## Visualization Catalog

### 1. Risk/Reward Quadrant

Purpose: Position theses in two-dimensional analytical space.

Question answered: Where does this thesis sit relative to
others in the portfolio?

Axes: Configurable by analyst.
Default: Business Quality (X) vs Margin of Safety (Y)
Alternatives: Confidence/CAGR, Evidence Strength/Strategic
Importance, Historical Accuracy/Framework Confidence.

Data source: pillar_scores, decision_logs, evidence_items.
Governed data only.

Interactions:
- Hover point: open thesis card
- Click point: navigate to thesis workspace
- Axis selector: change analytical dimensions

Constitutional constraints:
- Read only
- No governed artifacts created

---

### 2. Evidence Landscape

Purpose: Show which evidence is driving the decision.

Question answered: What evidence actually matters here?

Axes: Evidence Strength (X) vs Strategic Importance (Y)
Points: Individual promoted evidence items.

Data source: evidence_items, pillar_evidence_links.

Interactions:
- Hover point: open evidence card
- Click theme label: illuminate related evidence points
- Click point: navigate to evidence detail

Constitutional constraints:
- Read only
- Promoted evidence only — never staging records

---

### 3. Confidence Cone

Purpose: Calibration instrument for the analytical framework.

Question answered: How well calibrated is Athena across
its portfolio of completed decisions?

Structure:
- Cone predicted at decision time from analyst confidence
  and falsification trigger inputs
- Actual outcome plotted by Mnemosyne after review horizons
- Cone narrows as evidence accumulates before decision

Data source: decision_logs, thesis_reviews, pillar_scores.

Interactions:
- Hover any point on cone boundary: show evidence state
  at that moment
- Hover actual outcome point: show Mnemosyne attribution

Constitutional constraints:
- Advisory only
- Does not modify any decision record
- Mnemosyne comparison is observational
- Framework changes still require governed process

---

### 4. Scenario Projection

Purpose: Visualize bull, base, and bear trajectories.

Question answered: What range of outcomes does this thesis
support given current evidence and assumptions?

Structure:
- Three trajectories as confidence bands, not straight lines
- Tied to analyst falsification triggers and confidence inputs
- Updates when analyst changes assumptions

Data source: pillar_scores, decision_logs, analyst inputs.

Constitutional constraints:
- Advisory only
- Projections never become governed artifacts
- Changing assumptions does not modify existing scores

---

### 5. Thesis Trajectory

Purpose: Show the evolution of conviction over time.

Question answered: How did this thesis become what it is?

Structure:
- X: Time  Y: Composite conviction score
- Each point represents a governed event:
  evidence promoted, observation created, pillar scored,
  decision recorded, review completed
- Hover opens: what changed, what evidence was added,
  what the analyst recorded at that moment

Data source: thesis_events, evidence_items,
evidence_observations, pillar_scores, decision_logs,
thesis_reviews.

Interactions:
- Hover any point: expand governed event detail
- Click any point: navigate to that moment in the audit trail

Constitutional constraints:
- Read only
- Renders audit trail — never modifies it
- This is Athena's signature visualization

---

### 6. Outcome Attribution Timeline

Purpose: Visual Mnemosyne review history.

Question answered: What did each review horizon reveal?

Structure:
- Horizontal timeline from decision date through review horizons
- Each point: date, attribution type, brief narrative
- Pending horizons shown as open circles with action button

Data source: decision_logs, thesis_reviews.

Constitutional constraints:
- Pending review action button is the only interactive
  element that triggers a governed action
- All other interactions read only

---

### 7. Portfolio Position Map

Purpose: Show all theses in governed state space simultaneously.

Question answered: Where does the entire portfolio stand?

Structure:
- Each thesis as a point in configurable two-dimensional space
- Color communicates constitutional state
- Size communicates evidence completeness

Data source: theses, pillar_scores, decision_logs,
thesis_reviews.

Constitutional constraints:
- Read only
- No portfolio-level governed artifacts

---

### 8. Decision Surface

Purpose: Show the analytical decision space.

Question answered: How close is this thesis to a
decision boundary? Why would the recommendation change?

Structure:
- Contour plot
- X: Business Quality  Y: Margin of Safety
- Color gradient: Expected Outcome
- Current thesis as gold point on the surface
- Point moves as analyst changes assumptions

Data source: pillar_scores, analyst inputs.

Constitutional constraints:
- Advisory only
- Surface movement does not modify any score or decision
- Complements Confidence Cone by explaining why
  a recommendation changes

---

### 9. Framework Calibration Dashboard

Purpose: Measure Athena's analytical calibration across
its portfolio of completed decisions.

Question answered: How well does the framework perform?

Structure:
- Requires minimum completed validations before rendering
- Bull/Base/Bear scenario frequency distribution
- Confidence interval calibration chart
- Pillar predictive accuracy ranking
- Falsification trigger effectiveness
- Systematic underperformance identification

Data source: decision_logs, thesis_reviews, pillar_scores.
Powered by Mnemosyne.

Constitutional constraints:
- Advisory only — observational instrument
- Never triggers automatic framework changes
- Framework evolution still requires governed process
- Mnemosyne becomes a governed feedback mechanism,
  not an autonomous decision engine

---

## Implementation Notes

MVP-034 implements this specification.
Requires stable v2.0 foundation.
Each visualization is implemented as a separate component
following the Component Library patterns.
No visualization component contains business logic.
All data is fetched through service layer functions.
