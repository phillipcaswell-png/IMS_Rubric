<!-- Status: Superseded by ATHENA_DESIGN_SYSTEM.md -->

Document Authority: Versioned
Governed By: IMS Charter v1.0
Document Owner: Athena Product Design
Current Version: 1.0
Effective Date: June 2026
Purpose: Define the visual design language for the Athena platform.
Scope: Color, typography, iconography, motion, spacing, card anatomy,
       progressive disclosure, agent attribution, and accessibility.
May Modify: UI presentation layer only.
May Not Modify: Constitutional architecture, service layer, agent
                responsibilities, or governed workflow behavior.
Dependencies:
- IMS Charter v1.0
- ATHENA_ARCHITECTURE.md
Supersedes: None
Superseded By:

# Athena Design System

## Design Philosophy

Athena's visual language reinforces its constitutional philosophy.
Every design decision should communicate one of three things:

1. What type of information this is (evidence, synthesis, governance, memory)
2. Who produced it (Theia, Athena, Themis, Hermes, Mnemosyne)
3. What authority it carries (advisory, governed, immutable)

The design does not decorate the interface.
The design is the interface.

---

## Color System

### Palette

| Token | Value | Meaning |
|-------|-------|---------|
| athena-bg | #0A0A0F | Main background. Near black, slightly blue-tinted. |
| athena-surface | #12121A | Cards, panels, containers. |
| athena-border | #1E1E2E | Dividers, input borders. |
| athena-text-primary | #E8E6E0 | Main text. Warm white, like aged parchment. |
| athena-text-secondary | #8B8B9A | Secondary labels, metadata, captions. |
| athena-accent | #C5A028 | Athenian gold. Governed authority only. |
| athena-success | #2E7D52 | Constitutional approval, promoted state. |
| athena-warning | #8B6914 | Amber. Governance caution, analyst attention required. |
| athena-danger | #7D2E2E | Deep red. Constitutional block, gate failure. |

### Gold Is Governed Authority

The accent color #C5A028 appears only when something constitutional
is happening. It is not used for decoration, emphasis, or branding.

Gold appears on:
- Active constitutional step in the workflow
- Themis governance markers and decision gates
- Governed observation labels
- Final decision confirmation
- Key navigation active state
- The governance citation line

Gold does not appear on:
- Generic UI elements
- Decorative borders or backgrounds
- Informational text that carries no constitutional authority

When an analyst sees gold, they know something governed is present.
That meaning must be preserved as the platform grows.

---

## Typography

### Font Stacks

Headings (thesis names, pillar titles, section headers):
  "Cormorant Garamond", "Playfair Display", Georgia, serif
  Weight: 300–400. Letter spacing: 0.03em.
  Conveys authority without aggression.

Body (descriptions, labels, form text, analysis fields):
  Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
  Weight: 400. Line height: 1.6.
  Optimized for long reading under analytical conditions.

Metadata (IDs, dates, scores, grades, counts, status):
  "JetBrains Mono", "SFMono-Regular", Consolas, monospace
  Size: 0.85em. Color: secondary.
  Signals: this is a system value, not human prose.

### Type Scale

| Level | Size | Family | Usage |
|-------|------|--------|-------|
| Page title | 2.8rem | Serif, 300 | Athena wordmark |
| Section header | 1.6rem | Serif, 400 | Tab names, major sections |
| Subheader | 1.2rem | Serif, 400 | Pillar names, card titles |
| Body | 1rem | Sans-serif | All reading content |
| Label | 0.9rem | Sans-serif, 500 | Form labels |
| Caption | 0.8rem | Monospace | Metadata, IDs, dates |
| Agent label | 0.75rem | Monospace, uppercase | Agent attribution |

---

## Icon System

### Agent Symbols

Each agent has one symbol. The symbol communicates the constitutional
role of the information, not just the agent name.

| Agent | Symbol | Concept | Constitutional Meaning |
|-------|--------|---------|----------------------|
| Theia | Radiant eye | Perception | Raw observation. Fact before interpretation. |
| Athena | Owl | Wisdom | Evidence synthesis. Signal separated from noise. |
| Themis | Gavel (alone) | Governance | Decision authority. Constitutional gate. Immutable lock. |
| Hermes | Winged caduceus | Coordination | Workflow routing. Right information to right place. |
| Mnemosyne | Concentric ring | Memory | Historical preservation. Learning without rewriting. |

Greek subtitles appear beneath agent names in attribution contexts:
  Theia → ΘΕΙΑ
  Athena → ΑΘΗΝΑ
  Themis → ΘΕΜΙΣ
  Hermes → ΕΡΜΗΣ
  Mnemosyne → ΜΝΗΜΟΣΥΝΗ

### Icon Principles

- Monoline. Single stroke weight throughout.
- Geometric. Timeless and neutral.
- Meaningful. Rooted in classical symbolism.
- Consistent. 24x24px grid, 2px stroke at 24px, scales to 16px and 32px.

### Themis Icon Rule

The Themis symbol is the gavel alone — no columns, no courthouse.
The courthouse composition is reserved for documentation and
design materials only. In the UI at 16–20px, the gavel communicates
authority immediately and scales cleanly.

### Phase Implementation

Phase A (MVP-028): Text labels only for agent attribution.
  Format: "Theia · Observation" in uppercase monospace gold.

Phase B (MVP-029): Replace text labels with SVG icons.
  Each icon created on 24x24 grid, 2px stroke, monoline.

---

## Constitutional Workflow as Visual Sequence

The design reinforces the constitutional sequence:
