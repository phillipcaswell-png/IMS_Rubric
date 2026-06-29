<!-- Status: Active Standard -->

Document Authority: Versioned
Version: 1.0
Status: Active
Owner: Athena Product Design
Governed By: IMS Charter v1.0
Last Approved: June 2026
Purpose: Define the phased implementation roadmap for MVP-028
         Athena Experience.
Scope: Phase sequence, deliverables, and acceptance criteria
       for UI implementation. This document is expected to evolve.
       The other design documents remain comparatively stable.
Dependencies:
- IMS Charter v1.0
- ATHENA_UX_PRINCIPLES.md
- ATHENA_INTERFACE_MOCKUP.md
- ATHENA_COMPONENT_LIBRARY.md
Supersedes: None
Superseded By:

# Athena Experience — Implementation Plan

## Governing Constraint

No implementation phase may modify:
- Constitutional architecture
- Service layer
- Agent responsibilities
- Governed workflow behavior
- Database schema

Every phase modifies streamlit_app.py only unless
explicitly stated otherwise.

Every phase is independently reviewable and independently
reversible.

---

## Phase A — Typography and Color System
Status: Complete (v1.8.0)

Deliverables:
- Single centralized CSS block injected after st.set_page_config()
- Dark palette applied to background, sidebar, inputs, buttons, tabs
- Serif heading typography established
- Gold governance citation line

Acceptance Criteria:
- App starts without errors
- Dark background visible throughout
- Gold accent on buttons and active states
- No functional regressions

---

## Phase B — Navigation Redesign

Deliverables:
- Sidebar reduced to four items: Workspace, Theses, History, Settings
- Active thesis indicator below navigation items
- No emoji in navigation
- Sidebar styling consistent with design system

Acceptance Criteria:
- Navigation shows exactly four items
- Active thesis name visible below navigation
- All existing navigation destinations still work
- No functional regressions

---

## Phase C — Workspace Home Screen

Deliverables:
- render_thesis_card() component
- render_kpi_tile() component
- Workspace screen shows hero thesis card
- Today's Focus section
- Portfolio summary in secondary position

Acceptance Criteria:
- Active thesis appears as hero card
- Hero statement (thesis question) visible
- Three progress bars: Evidence, Assessment, Decision
- Portfolio summary below hero
- No competing cards on home screen
- No functional regressions

---

## Phase D — Thesis Overview and Constitutional Journey

Deliverables:
- render_progress_journey() component
- render_hero_banner() component
- Thesis overview shows constitutional journey
- Four stages with agent attribution labels
- Athena Pre-Brief below the journey

Acceptance Criteria:
- Four constitutional stages visible in order
- Active stage highlighted in gold
- Agent attribution labels present on each stage
- Athena Pre-Brief renders below journey
- One primary action button
- No functional regressions

---

## Phase E — Evidence Mode Card Layout

Deliverables:
- render_evidence_card() component
- render_agent_attribution() component
- render_empty_state() component
- Evidence mode shows cards not table
- Staging queue collapsed by default

Acceptance Criteria:
- Document name leads every card
- Excerpt visible in card body
- Agent attribution in card footer
- Staging queue collapsed with item count
- Cards ordered by publication date
- All evidence operations still function
- No functional regressions

---

## Phase F — Assessment Mode Progressive Scoring

Deliverables:
- render_pillar_navigator() component
- render_synthesis_panel() component
- render_judgment_form() component
- One pillar visible at a time
- Synthesis panel above judgment form
- Previous and next navigation with pillar labels

Acceptance Criteria:
- Only one pillar visible at a time
- Pillar navigator shows completion state
- Synthesis panel renders above judgment form
- Governed observations before advisory signals
- ANALYST JUDGMENT header used
- Scoring saves correctly
- No functional regressions

---

## Phase G — Decision Mode Themis Gate

Deliverables:
- render_governance_gate() component
- render_governance_gate_action() component
- render_modal_confirmation() component
- render_decision_record() component
- Eligibility gate above recommendation form
- Action gate below recommendation form
- Record Decision button as sole gold element

Acceptance Criteria:
- Eligibility gate shows all 11 pillars complete
- Recommendation form renders between gates
- Record Decision is the only gold button
- Immutability warning present and explicit
- ⊘ symbol on record button
- Decision records correctly and locks
- No functional regressions

---

## Phase H — Mnemosyne Timeline

Deliverables:
- render_timeline() component
- Mnemosyne mode shows chronological timeline
- Complete reviews show attribution type and narrative
- Pending reviews show single action button

Acceptance Criteria:
- Timeline flows chronologically top to bottom
- Decision recorded appears as first timeline point
- Complete reviews show ● filled circle
- Pending reviews show ○ empty circle
- Attribution type on every complete review
- Outcome recording still functions
- No functional regressions

---

## Phase I — Icon SVG Integration (MVP-029)

Deliverables:
- Five production SVG icons integrated throughout UI
- [theia.svg] [athena.svg] [themis.svg]
  [hermes.svg] [mnemosyne.svg]
- Emoji and text placeholders replaced
- Icons color-controlled via CSS stroke property

Acceptance Criteria:
- Icons render at 16px 20px 24px 32px without degradation
- Icons are gold (#C5A028) by default
- Icons can be recolored via CSS for status variants
- No functional regressions

---

## Standard Prompt Structure

Every implementation prompt follows this governed sequence.

L1 Prompts:
  Inspection optional
  Phase 1: Implementation → Verify → Report → STOP
  Phase 2: Review → Approve → Commit → Tag if milestone

L2 Prompts:
  Phase 0: Inspect → Report → STOP → Wait for approval
  Phase 1: Implement → Verify → Report → STOP
  Phase 2: Review → Approve → Commit → Tag if milestone

L3 Prompts:
  Phase 0: Inspect → Report → STOP → Wait for approval
  Phase 1: Implement → Verify → Report → STOP
  Phase 2: Review → Approve → Commit → Tag if milestone
  Phase 3: Validate against historical reference case
           before commit authorization

Verification stays with Implementation.
Review decides whether the verified implementation
becomes part of the project.
Commit requires explicit approval after review.

---
