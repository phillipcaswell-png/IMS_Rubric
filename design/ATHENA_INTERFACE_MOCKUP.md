Document Authority: Versioned
Version: 1.0
Status: Frozen
Owner: Athena Product Design
Governed By: IMS Charter v1.0
Last Approved: June 2026
Purpose: Define the screen layouts and user experience for
         every Athena Mode.
Scope: Screen-by-screen layouts, hero statements, navigation
       structure, and mode transitions. No component anatomy.
       No implementation notes. No CSS.
Dependencies:
- IMS Charter v1.0
- ATHENA_UX_PRINCIPLES.md
- ATHENA_DESIGN_SYSTEM.md
- ATHENA_COMPONENT_LIBRARY.md
Supersedes: None
Superseded By:

# Athena Experience — Interface Mockup

## Mode Structure

Athena does not use tabs. It uses Modes.
Each Mode corresponds directly to a constitutional stage.
```
Workspace Mission control. Active thesis hero. Evidence Perception. Gather what was knowable. Assessment Understanding. Transform evidence to judgment. Decision Judgment. Record what becomes history. Mnemosyne Memory. Learn without rewriting the past.

```
The UI and the constitutional philosophy are identical.
Moving through Modes is moving through the governed process.

---

## Navigation System
```
Athena ──────────────────────────── Workspace Theses History Settings

──────────────────────────── Active Eastman Kodak ⬤ In Progress

```
Rules:
- Four navigation items only
- No emoji in navigation
- No sub-menus visible by default
- Active thesis name below the four items
- Greek names do not appear in navigation

---

## Greek Name Policy

Greek names (ΘΕΙΑ, ΑΘΗΝΑ, ΘΕΜΙΣ, ΕΡΜΗΣ, ΜΝΗΜΟΣΥΝΗ)
are reserved for:
  - Splash screen
  - About dialog
  - Agent information popovers
  - Documentation and design materials
  - Hover tooltips
  - Empty states

The operational interface uses English names only:
  Theia · Observation
  Athena · Synthesis
  Themis · Governance
  Hermes · Coordination
  Mnemosyne · Review

---

## Screen 1 — Workspace

Question this screen answers: What are you doing today?

Hero statement: Your work. Your focus. Right now.
```
┌─────────────────────────────────────────────────────────────┐ │ │ │ Athena [+ New Thesis] │ │ GOVERNED INVESTMENT INTELLIGENCE │ │ [themis.svg] Governed by Athena Charter v1.0 │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ Continue Working │ │ │ │ Eastman Kodak Company │ │ Historical Validation │ │ │ │ Can Athena identify structural regime change │ │ using only contemporaneous evidence? │ │ │ │ Evidence ██████████ Complete │ │ Assessment █████░░░░░ 3 of 7 │ │ Decision ░░░░░░░░░░ Not eligible │ │ │ │ [Continue →] │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ Today's Focus │ │ · 4 Business pillars remaining │ │ · Decision not yet eligible │ │ · Next milestone: Themis Governance │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ Portfolio │ │ 6 Active · 2 Awaiting Review · 1 Validation Complete │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Hero thesis always appears first
- Thesis question in italic serif beneath company name
- Progress bars: Evidence, Assessment, Decision only
- Today's Focus: three most important next actions
- Portfolio summary: last, smallest, secondary text
- No competing thesis cards on this screen
- If no active thesis: show [Begin New Thesis] as the hero

---

## Screen 2 — Thesis Overview

Question this screen answers: Where does this thesis stand?

Hero statement: Every thesis has a constitutional journey.
```
┌─────────────────────────────────────────────────────────────┐ │ ← Workspace Eastman Kodak Company │ │ EK · Historical Validation │ │ Cutoff 30 September 2000 │ │ │ │ Can Athena identify structural regime change │ │ using only contemporaneous evidence? │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ THE CONSTITUTIONAL JOURNEY │ │ │ │ [theia.svg] Perception ✓ Complete │ │ Evidence Collection │ │ 3 filings promoted │ │ │ │ ↓ │ │ │ │ [athena.svg] Understanding ⬤ In Progress │ │ Business Assessment │ │ 3 of 7 pillars complete │ │ │ │ ↓ │ │ │ │ [themis.svg] Judgment ○ Pending │ │ Governed Decision │ │ Awaiting assessment completion │ │ │ │ ↓ │ │ │ │ [mnemosyne.svg] Memory ○ Pending │ │ Mnemosyne · Historical Review │ │ Not yet eligible │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ [athena.svg] Athena · Pre-Brief │ │ │ │ Three Phase 1A filings promoted. Digital substitution │ │ risk disclosed in all three. B1-B3 scored. B4-B7 │ │ require assessment before decision is eligible. │ │ │ │ Next governed action: Complete Business Assessment │ │ │ │ [Continue Assessment →] │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Hero statement beneath thesis header always
- Four constitutional stages in order with agent icons
- Active stage highlighted in gold
- Complete: ✓  In Progress: ⬤ gold  Pending: ○ secondary
- Athena Pre-Brief below the journey
- One primary action button

---

## Screen 3 — Evidence Mode

Question this screen answers: What have you gathered?

Hero statement: Gather only what was knowable before the decision.
```
┌─────────────────────────────────────────────────────────────┐ │ Eastman Kodak · Evidence │ │ │ │ Gather only what was knowable before the decision. │ │ [+ Add] │ │ │ │ PROMOTED EVIDENCE │ │ │ │ ┌─────────────────────────────────────────────────────┐ │ │ │ │ │ │ │ Kodak 1999 Annual Report │ │ │ │ Form 10-K · 15 March 2000 │ │ │ │ │ │ │ │ ───────────────────────────────────────────── │ │ │ │ │ │ │ │ Consumer Imaging segment disclosed accelerating │ │ │ │ digital substitution and transition risk before │ │ │ │ the evidence cutoff. │ │ │ │ │ │ │ │ ───────────────────────────────────────────── │ │ │ │ │ │ │ │ [theia.svg] Theia · Observation │ │ │ │ Grade A · Promoted [View ›] │ │ │ └─────────────────────────────────────────────────────┘ │ │ │ │ ▸ Staging Queue (2 pending review) │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Hero statement immediately below mode header
- Document name leads every card — never evidence ID
- Filing type and date on second line in monospace secondary
- Excerpt in middle, 2-3 lines maximum
- Agent attribution in footer with production icon reference
- Staging queue collapsed by default with item count
- Cards ordered by publication date ascending

---

## Screen 4 — Assessment Mode · Business Quality

Question this screen answers: What does this pillar tell you?

Hero statement: Transform evidence into disciplined judgment.
```
┌─────────────────────────────────────────────────────────────┐ │ Eastman Kodak · Assessment │ │ │ │ Transform evidence into disciplined judgment. │ │ │ │ B1 ✓ B2 ✓ B3 ✓ B4 · B5 · B6 · B7 · │ │ ▲ │ │ ───────────────────────────────────────────────────── │ │ │ │ B4 FINANCIAL RESILIENCE │ │ │ │ [athena.svg] Athena · Synthesis │ │ ───────────────────────────────────────────────────── │ │ │ │ GOVERNED OBSERVATIONS │ │ · Film infrastructure represents significant fixed │ │ cost base. Risk if digital substitution accelerates. │ │ — Kodak 1999 10-K · Governed Observation │ │ │ │ ADVISORY SIGNALS │ │ · Restructuring charges recorded Q2 2000. │ │ — Kodak Q2 2000 10-Q · Advisory │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ ANALYST JUDGMENT │ │ │ │ Score [ 1 2 3 4 5 6 7 8 9 10 ] │ │ Confidence [ High ▼ ] │ │ │ │ Judgment │ │ ┌──────────────────────────────────────────────────────┐ │ │ │ │ │ │ └──────────────────────────────────────────────────────┘ │ │ │ │ Falsification Trigger │ │ ┌──────────────────────────────────────────────────────┐ │ │ │ │ │ │ └──────────────────────────────────────────────────────┘ │ │ │ │ [← B3] [Save · Next: B5 →] │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Hero statement below mode header
- One pillar visible at a time — never all seven
- Pillar dots: ✓ complete, · pending, ▲ active indicator
- Athena Synthesis always above Analyst Judgment
- Governed Observations always before Advisory Signals
- Section header is ANALYST JUDGMENT — never Your Assessment
- Previous and Next show pillar labels

---

## Screen 5 — Assessment Mode · Investment Assessment

Question: What are the investment conditions?

Hero statement: Transform evidence into disciplined judgment.

Same progressive structure as Business Quality.
One pillar at a time. Athena context above. Analyst Judgment below.
I1 through I4 with identical navigation pattern.

---

## Screen 6 — Decision Mode

Question this screen answers:
Is this decision constitutionally ready to become history?

Hero statement: Record only decisions worthy of becoming history.
```
┌─────────────────────────────────────────────────────────────┐ │ Eastman Kodak · Decision │ │ │ │ Record only decisions worthy of becoming history. │ │ │ │ Can Athena identify structural regime change │ │ using only contemporaneous evidence? │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ [themis.svg] Themis · Governance Gate │ │ │ │ All 11 pillars complete. │ │ Business Quality Average: 4.8 │ │ Investment Assessment Average: 3.2 │ │ This thesis is constitutionally eligible for decision. │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ GOVERNED RECOMMENDATION │ │ │ │ Recommendation [ Observe ▼ ] │ │ Conviction [ Medium ▼ ] │ │ │ │ Primary Thesis │ │ ┌──────────────────────────────────────────────────────┐ │ │ │ │ │ │ └──────────────────────────────────────────────────────┘ │ │ │ │ Key Risk │ │ ┌──────────────────────────────────────────────────────┐ │ │ │ │ │ │ └──────────────────────────────────────────────────────┘ │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ [themis.svg] Themis · Governance Gate │ │ │ │ This action permanently records the historical decision. │ │ It cannot be modified after recording. │ │ Validation configuration will be locked. │ │ │ │ ⊘ [ Record Decision ] │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Hero statement at top
- Thesis question beneath hero statement
- Themis gate appears twice: eligibility above, action below
- Record Decision button is the only gold button on screen
- Immutability warning always present in action section
- ⊘ symbol precedes the button label
- No other buttons compete with Record Decision

---

## Screen 7 — Mnemosyne Mode

Screen name: Mnemosyne
Subtitle: Historical Review

Question this screen answers: What did history reveal?

Hero statement: Learn without rewriting the past.
```
┌─────────────────────────────────────────────────────────────┐ │ Eastman Kodak · Mnemosyne │ │ Historical Review │ │ │ │ Learn without rewriting the past. │ │ │ │ [mnemosyne.svg] Mnemosyne · Memory │ │ │ │ Decision recorded 30 September 2000 │ │ Observe · Medium Conviction │ │ │ │ ───────────────────────────────────────────────────── │ │ │ │ TIMELINE │ │ │ │ 2000 ──●── Decision Recorded │ │ Observe · 30 Sep 2000 │ │ │ │ │ │ │ ▼ │ │ │ │ 2001 ──●── 1 Year Review ✓ │ │ Type D — Random Variation │ │ Stock declined as digital transition │ │ accelerated beyond expectations. │ │ │ │ │ │ │ ▼ │ │ │ │ 2003 ──●── 3 Year Review ✓ │ │ Type C2 — Structural Regime Change │ │ Digital photography became dominant. │ │ Film revenue declined structurally. │ │ │ │ │ │ │ ▼ │ │ │ │ 2005 ──○── 5 Year Review · Pending │ │ [Record 5 Year Outcome] │ │ │ └─────────────────────────────────────────────────────────────┘

```
Rules:
- Screen name is Mnemosyne with subtitle Historical Review
- Hero statement immediately below screen header
- Mnemosyne attribution appears once at the top
- Timeline flows chronologically top to bottom
- ● filled for complete  ○ empty for pending
- Decision recorded is always the first timeline point
- Attribution type on every complete review
- Narrative 1-2 sentences maximum per review
- Pending review shows one action button only
