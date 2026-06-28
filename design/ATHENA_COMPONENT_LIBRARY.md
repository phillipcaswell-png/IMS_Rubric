Document Authority: Versioned
Version: 1.0
Status: Frozen
Owner: Athena Product Design
Governed By: IMS Charter v1.0
Last Approved: June 2026
Purpose: Define every reusable UI component for the Athena Experience.
Scope: Component anatomy, rules, variants, usage constraints,
       and Python rendering function signatures.
Dependencies:
- IMS Charter v1.0
- ATHENA_UX_PRINCIPLES.md
- ATHENA_DESIGN_SYSTEM.md
Supersedes: None
Superseded By:

# Athena Component Library

## Principles

Every component in this library:
- Accepts only the data it needs to render
- Contains no business logic
- Makes no database calls
- Returns no governed artifacts
- Is purely presentational

Service layer owns logic. Components own rendering.

---

## Component Index

1.  Hero Banner             render_hero_banner()
2.  Thesis Card             render_thesis_card()
3.  Evidence Card           render_evidence_card()
4.  Agent Attribution       render_agent_attribution()
5.  Athena Synthesis Panel  render_synthesis_panel()
6.  Themis Governance Gate  render_governance_gate()
7.  Mnemosyne Timeline      render_timeline()
8.  Progress Journey        render_progress_journey()
9.  Pillar Navigator        render_pillar_navigator()
10. Analyst Judgment Form   render_judgment_form()
11. KPI Tile                render_kpi_tile()
12. Status Badge            render_status_badge()
13. Decision Record Panel   render_decision_record()
14. Empty State             render_empty_state()
15. Modal Confirmation      render_modal_confirmation()

---

## 1. Hero Banner

render_hero_banner(company, thesis_type, cutoff, hero_statement)

Purpose: Establishes the primary focus of any screen.
Appears: Workspace, Thesis Overview, all Mode screens.
```
[Company Name] [Thesis Type] · [Cutoff Date]

[Hero Statement — italic serif]

```
Rules:
- Company name: serif 1.6rem weight 300
- Thesis type and metadata: monospace secondary 0.8rem
- Hero statement: serif italic 1rem primary color
- Hero statement is never omitted
- Hero statement is the thesis question or investment thesis

---

## 2. Thesis Card

render_thesis_card(company, thesis_type, hero_statement,
                   evidence_pct, assessment_pct, decision_pct,
                   status)

Purpose: Represents one thesis in workspace or thesis list.
```
┌─────────────────────────────────────────────────────────────┐ │ [Company Name] [Status Badge] │ │ [Thesis Type] │ │ │ │ [Hero Statement — italic] │ │ │ │ Evidence [████████░░] │ │ Assessment [█████░░░░░] │ │ Decision [░░░░░░░░░░] │ │ │ │ [Continue →] │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Three progress bars only
- Continue button is gold
- Card background: #12121A  border: #1E1E2E  radius: 6px

---

## 3. Evidence Card

render_evidence_card(title, filing_type, publication_date,
                     excerpt, grade, status)

Purpose: Represents one promoted evidence item.
```
┌─────────────────────────────────────────────────────────────┐ │ │ │ [Document Name] │ │ [Filing Type] · [Publication Date] │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ [Excerpt — 2-3 lines] │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ [theia.svg] Theia · Observation │ │ [Grade Badge] · [Status Badge] [View ›] │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Document name leads — never evidence ID
- Excerpt: sans-serif 0.9rem 2-3 lines maximum
- Agent attribution in footer with icon reference
- Cards ordered by publication date ascending

---

## 4. Agent Attribution Label

render_agent_attribution(agent, role)

Purpose: Identifies agent and authority level of information.
```
[icon.svg] AGENT NAME · ROLE

```
Format:
- All caps monospace gold #C5A028
- 0.75rem letter-spacing 0.12em
- Icon precedes label
- Greek names never appear in operational interface

Variants:
```
[theia.svg] THEIA · OBSERVATION [athena.svg] ATHENA · SYNTHESIS [themis.svg] THEMIS · GOVERNANCE [hermes.svg] HERMES · COORDINATION [mnemosyne.svg] MNEMOSYNE · REVIEW

```
Rules:
- Attribution label appears once per panel
- Never appears without content beneath it

---

## 5. Athena Synthesis Panel

render_synthesis_panel(pillar_id, pillar_label,
                       governed_observations, advisory_signals)

Purpose: Displays governed observations and advisory signals
         organized by pillar before analyst scoring.
```
┌─────────────────────────────────────────────────────────────┐ │ [athena.svg] Athena · Synthesis │ │ │ │ GOVERNED OBSERVATIONS │ │ · [observation_text] │ │ — [evidence_title] · Governed Observation │ │ │ │ ADVISORY SIGNALS │ │ · [signal_text] │ │ — [evidence_title] · Advisory │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Governed Observations always before Advisory Signals
- Source attribution on every item
- "Governed Observation" label on every governed item
- "Advisory" label on every advisory item
- Labels never blurred or omitted
- Panel is read-only — no interactive elements
- Panel background: #12121A with gold left border 3px

---

## 6. Themis Governance Gate

render_governance_gate(eligible, blockers, averages)
render_governance_gate_action(immutability_warning)

Purpose: Constitutional eligibility check and decision action.
Appears: Decision Mode — eligibility variant above form,
         action variant below form.

Eligibility variant:
```
┌─────────────────────────────────────────────────────────────┐ │ [themis.svg] Themis · Governance Gate │ │ │ │ [Eligibility status] │ │ [Scores if eligible] │ │ [Blockers listed if not eligible] │ └─────────────────────────────────────────────────────────────┘

```
Action variant:
```
┌─────────────────────────────────────────────────────────────┐ │ [themis.svg] Themis · Governance Gate │ │ │ │ This action permanently records the historical decision. │ │ It cannot be modified after recording. │ │ Validation configuration will be locked. │ │ │ │ ⊘ [ Record Decision ] │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Record Decision button is gold — only gold button on screen
- Immutability warning always present in action variant
- ⊘ symbol precedes button label
- Not eligible: border becomes #8B6914 amber
- Blockers listed explicitly

---

## 7. Mnemosyne Timeline

render_timeline(decision_record, reviews)

Purpose: Displays historical review sequence chronologically.
```
[Year] ──●── [Event Title] [Attribution Type] [Narrative 1-2 sentences]

```
           │
           ▼
```
[Year] ──○── [Pending Title] [Record button]

```
Rules:
- ● complete  ○ pending
- Decision recorded is always the first point
- Attribution type on every complete review
- Narrative 1-2 sentences maximum
- Pending shows one action button only
- Read-only except pending action buttons

---

## 8. Progress Journey

render_progress_journey(evidence_status, assessment_status,
                         judgment_status, memory_status)

Purpose: Four constitutional stages with status.
```
[theia.svg] Perception ✓ Complete Evidence Collection [detail]

```
            ↓
```
[athena.svg] Understanding ⬤ In Progress Business Assessment [detail]

```
            ↓
```
[themis.svg] Judgment ○ Pending Governed Decision [detail]

```
            ↓
```
[mnemosyne.svg] Memory ○ Pending Mnemosyne · Historical Review [detail]

```
Rules:
- Four stages always shown in order
- Active stage highlighted in gold
- Complete ✓  In Progress ⬤ gold  Pending ○ secondary

---

## 9. Pillar Navigator

render_pillar_navigator(pillars, active_pillar)

Purpose: Shows pillar completion and enables navigation.

Business Quality:
```
B1 ✓ B2 ✓ B3 ✓ B4 · B5 · B6 · B7 · ▲

```
Investment Assessment:
```
I1 ✓ I2 ✓ I3 · I4 · ▲

```
Rules:
- ✓ complete in success green
- · pending in secondary color
- ▲ active indicator in gold below active pillar
- Complete pillars are navigable
- Pending pillars navigate to next required

---

## 10. Analyst Judgment Form

render_judgment_form(pillar_id, pillar_label,
                     existing_score, prev_pillar, next_pillar)

Purpose: Captures analyst scored assessment for one pillar.
```
ANALYST JUDGMENT

Score [ 1 2 3 4 5 6 7 8 9 10 ]

Confidence [ High ▼ ]

Judgment ┌──────────────────────────────────────────────────────────┐ │ │ └──────────────────────────────────────────────────────────┘

Falsification Trigger ┌──────────────────────────────────────────────────────────┐ │ │ └──────────────────────────────────────────────────────────┘

[← Previous Pillar] [Save · Next Pillar →]

```
Rules:
- Section header: ANALYST JUDGMENT — never Your Assessment
- Score: 1-10 only
- All four fields required before Save enables
- Navigation shows actual pillar labels
- Save button gold only when all fields complete

---

## 11. KPI Tile

render_kpi_tile(value, label)

Purpose: Single metric in secondary position.
```
┌──────────────┐ │ 6 │ │ Active │ └──────────────┘

```
Rules:
- Number: monospace gold 1.8rem
- Label: sans-serif secondary 0.8rem
- Never leads the screen — always secondary
- Maximum three tiles visible at once

---

## 12. Status Badge

render_status_badge(status)

Variants:
- Promoted      — #2E7D52 background
- Pending       — #8B6914 background
- Rejected      — #7D2E2E background
- Archived      — #8B8B9A background
- In Progress   — gold border transparent background
- Complete      — green border transparent background
- Eligible      — #C5A028 background dark text
- Locked        — #8B8B9A secondary

Rules:
- Monospace uppercase 0.7rem
- Border radius 3px  padding 2px 6px
- Never color as sole indicator — always include text label

---

## 13. Decision Record Panel

render_decision_record(date, recommendation, conviction)

Purpose: Read-only display of a locked decision.
```
┌─────────────────────────────────────────────────────────────┐ │ [themis.svg] Themis · Governance │ │ │ │ Decision Recorded │ │ [Date] · [Recommendation] · [Conviction] │ │ │ │ ⊘ Immutable · Validation configuration locked │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- ⊘ signals immutability
- Read-only — no edit controls
- Gold left border  surface background
- Immutable label always present

---

## 14. Empty State

render_empty_state(agent, title, greek_subtitle,
                   explanation, action_label)

Purpose: Guides analyst when no content is available.
```
┌─────────────────────────────────────────────────────────────┐ │ │ │ [icon.svg large] │ │ [Agent Name] │ │ [Greek subtitle — permitted in empty states only] │ │ │ │ [One explanation sentence] │ │ │ │ [Primary action button] │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Greek subtitles permitted in empty states only
- One explanation sentence
- One action button
- Icon centered larger than operational attribution size

---

## 15. Modal Confirmation

render_modal_confirmation(title, consequence, confirm_label)

Purpose: Explicit confirmation before constitutional action.
```
┌─────────────────────────────────────────────────────────────┐ │ │ │ [Action Title] │ │ │ │ [Consequence — what cannot be undone] │ │ │ │ [Cancel] [Confirm — gold] │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Confirm gold only for constitutional actions
- Cancel always present and never hidden
- Consequence statement explicit — never vague
- Escape activates Cancel

---

## Component Usage Matrix

| Component              | Workspace | Evidence | Assessment | Decision | Mnemosyne |
|------------------------|-----------|----------|------------|----------|-----------|
| Hero Banner            | ✓         | ✓        | ✓          | ✓        | ✓         |
| Thesis Card            | ✓         |          |            |          |           |
| Evidence Card          |           | ✓        |            |          |           |
| Agent Attribution      |           | ✓        | ✓          | ✓        | ✓         |
| Synthesis Panel        |           |          | ✓          |          |           |
| Governance Gate        |           |          |            | ✓        |           |
| Timeline               |           |          |            |          | ✓         |
| Progress Journey       | ✓         |          |            |          |           |
| Pillar Navigator       |           |          | ✓          |          |           |
| Judgment Form          |           |          | ✓          |          |           |
| KPI Tile               | ✓         |          |            |          |           |
| Status Badge           |           | ✓        |            | ✓        | ✓         |
| Decision Record        | ✓         |          |            | ✓        |           |
| Empty State            |           | ✓        | ✓          |          | ✓         |
| Modal Confirmation     |           |          |            | ✓        |           |
